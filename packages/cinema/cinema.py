#!/usr/bin/env python
# -*- coding:utf-8 -*-

import utils
import tmdbsimple as tmdb
import functools
import random as ran
import datetime as dt
import json

# Package database
db = utils.db()['db']

# Query
Query = utils.db()['query']()


def load_config(func):
    @functools.wraps(func)
    def wrapper_load_config(string, entities):
        # Init "payload" as dictionary
        payload = dict()
        # Put data in payload
        payload["string"] = string
        payload["entities"] = entities
        #  ISO 639-1 language code
        payload["lang"] = utils.getqueryobj()["lang"][:2]
        payload["today"] = dt.date.today()

        # Load API key
        payload["API_KEY"] = utils.config('API_KEY')
        tmdb.API_KEY = payload["API_KEY"]
        if payload["API_KEY"] == "YOUR_API_KEY":
            return utils.output("end", "wrong_key", utils.translate("wrong_key"))

        # Load words files who permit to check if user ask for a serie or a movie in every language
        with open('packages/cinema/data/words/movie.json') as json_data:
            payload["trl_movie"] = json.load(json_data)
        with open('packages/cinema/data/words/serie.json') as json_data:
            payload["trl_serie"] = json.load(json_data)

        return func(payload)

    return wrapper_load_config


@load_config
def recommend(payload):
    flag_movie = 0
    flag_serie = 0
    for item in payload["entities"]:
        if item["entity"] == "Serie_Or_Movie":
            word = item["sourceText"]
            i = 0
            wflag = 0
            while i < 92 and wflag == 0:
                if payload["trl_movie"][i]["string"] == word:
                    flag_movie = 1
                    wflag = 1
                elif payload["trl_serie"][i]["string"] == word:
                    flag_serie = 1
                    wflag = 1
                i = i + 1
        else:
            return utils.output('end', 'Error', utils.translate('Error'))

    if flag_movie == 1:
        if db.search(Query.type == 'rmovie_request'):
            payload["movie"] = db.search(Query.type == 'rmovie_request')[0]['content']
            o_id = db.search(Query.type == 'rmovie_request')[0]['old_id']
            o_id = o_id + 1
            db.update({"old_id": o_id}, Query.type == 'rmovie_request')
            db.remove(Query.type == 'rmovie_request' and Query.old_id > 10)
        else:
            # Get an random movie with user's language
            payload["movie"] = tmdb.Discover().movie(
            page=ran.randint(0, 1000),
            language=payload["lang"],
            vote_average_gte=7.00)
            db.insert({'type': 'rmovie_request','old_id': 0, 'content': payload["movie"]})

        movie_nO = ran.randint(0, 20)
        movie = payload["movie"]["results"][movie_nO]
        movie_title = movie["title"]
        movie_rdate = movie["release_date"]
        movie_sum = movie["overview"]

        return utils.output('end', 'recommend', utils.translate('recommend', {
        "movie_title": movie_title,
        "release_date": movie_rdate,
        "summarize": movie_sum}))

    elif flag_serie == 1:
        if db.search(Query.type == 'rserie_request'):
            payload["serie"] = db.search(Query.type == 'rserie_request')[0]['content']
            o_id = db.search(Query.type == 'rserie_request')[0]['old_id']
            o_id = o_id + 1
            db.update({"old_id": o_id}, Query.type == 'rserie_request')
            db.remove(Query.type == 'rserie_request' and Query.old_id > 10)
        else:
            # Get an random serie with user's language
            payload["serie"] = tmdb.Discover().tv(
            page=ran.randint(0, 1000),
            language=payload["lang"],
            vote_average_gte=7.00)
            db.insert({'type': 'rserie_request', 'old_id': 0, 'content': payload["serie"]})

        serie_nO = ran.randint(0, 20)
        serie = payload["serie"]["results"][serie_nO]
        serie_title = serie["name"]
        serie_rdate = serie["first_air_date"]
        serie_sum = serie["overview"]

        return utils.output('end', 'recommend', utils.translate('recommend', {
        "movie_title": serie_title,
        "release_date": serie_rdate,
        "summarize": serie_sum}))


@load_config
def now_theatres(payload):
    """
    Displays the list of recently released movies
    """
    #Ask API about movies
    now_in_theatres = tmdb.Discover().movie(
    primary_release_date=payload["today"],
    language=payload["lang"])
    res = 'The films currently in the cinema are: <br/><ul>'
    for title in now_in_theatres["results"]:
        res = res+"<li>"+title["title"]+"</li>"+"<br/>"
    res = res + "</ul>"

    return utils.output("end", "nit_title_list", utils.translate('nit_list', {
    "nit_title": res
    }))

@load_config
def info(payload):
    for item in payload["entities"]:
        if item["entity"] == "title":
            data_title = item["sourceText"]

    data_info = tmdb.Search().collection(query=data_title, language=payload["lang"])
    if data_info["total_results"] == 0:
            data_info = tmdb.Search().multi(query=data_title, language=payload["lang"])
            if data_info["results"][0]["media_type"] == "movie":
                movie_overview = data_info["results"][0]["overview"]
                movie_rdate = data_info["results"][0]["release_date"]
                movie_title = data_info["results"][0]["title"]

                return utils.output("end", "info-m", utils.translate("info-m", {
                "title": movie_title.title(),
                "release_date": movie_rdate,
                "overview": movie_overview
                }))
            elif data_info["results"][0]["media_type"] == "tv":
                tv_overview = data_info["results"][0]["overview"]
                tv_rdate = data_info["results"][0]["first_air_date"]
                tv_title = data_info["results"][0]["name"]

                return utils.output("end", "info-t", utils.translate("info-t", {
                "title": tv_title.title(),
                "release_date": tv_rdate,
                "overview": tv_overview
                }))
            elif data_info["results"][0]["media_type"] == "person":
                people_name = data_info["results"][0]["name"]
                title_know_for = data_info["results"][0]["known_for"][0]["title"]
                rdate_know_for = data_info["results"][0]["known_for"][0]["release_date"]

                return utils.output("end", "info-p", utils.translate("info-p", {
                "name": people_name.title(),
                "release_date": rdate_know_for,
                "maj-movie-title": title_know_for
                }))

    data_overview = data_info["results"][0]["overview"]

    return utils.output("end", "info-c", utils.translate('info', {
    "title": data_title.title(),
    "overview": data_overview}))
