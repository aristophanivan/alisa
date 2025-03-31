from flask import Flask, request, jsonify
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['965417/56d1f2eddb605502b942',
               '965417/fb5f90d5339cfc19910c'],
    'нью-йорк': ['13200873/d53af38e0d0021c2a8a6',
                 '1030494/c6f7cdc125120168ff9c'],
    'париж': ["13200873/1ea425ee9df49e9a49b7",
              '1540737/453aeb8b7882c5b2715c']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Поиграем в игру?'
            res['response']['buttons'] = [
                {
                    'title': "Да",
                    'hide': True
                },
                {
                    'title': "Нет",
                    'hide': True
                }
            ]
    else:
        if sessionStorage[user_id]['game_start'] is None:
            if "Нет" in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Да ладно?! Ну ладно.'
                res['response']['end_session'] = True
                return
            elif "Да" in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['cities']) == 3:
                    res['response']['text'] = 'Все города отгаданы'
                    res['response']['end_session'] = True
                    return
                else:
                    sessionStorage[user_id]['game_start'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)
            else:
                res['response']['buttons'] = [
                    {
                        'title': "Да",
                        'hide': True
                    },
                    {
                        'title': "Нет",
                        'hide': True
                    }
                ]

        city = get_city(req)
        if city in cities:

        else:
            res['response']['text'] = \
                'Первый раз слышу об этом городе. Попробуй еще разок!'


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]["attempt"]
    city = random.choice(list(set(cities) - set(sessionStorage[user_id][cities])))
    if attempt == 1:
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Угадай-ка, что за город?'
        res['response']['card']['image_id'] = cities[city][0]
        res['response']['text'] = 'Поиграем!'
        if get_city(req) == city:
            sessionStorage[user_id]['cities'].append(city)
            res['response']['text'] = 'Правильно. Сыграем еще?'
            sessionStorage[user_id]['game_start'] = False
            return
        else:
            res['response']['text'] = 'Есть вторая попытка!'
    else:
        res['response']['card']['image_id'] = cities[city][1]
        res['response']['text'] = 'Вторая попытка!'
        if get_city(req) == city:
            sessionStorage[user_id]['cities'].append(city)
            res['response']['text'] = 'Правильно. Сыграем еще?'
            sessionStorage[user_id]['game_start'] = False
            return
        else:
            sessionStorage[user_id]['cities'].append(city)
            res['response']['text'] = f'Жаль. Вы не угадали. Это был город {city.title()}'
            sessionStorage[user_id]['game_start'] = False
            return
    sessionStorage[user_id]['attempt'] += 1


if __name__ == '__main__':
    app.run()
