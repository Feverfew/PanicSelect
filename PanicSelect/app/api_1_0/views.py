from flask import Flask, jsonify, request
from . import api_1_0, models

def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def not_found():
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response


@api_1_0.route('/ratings')
def champions_rating():
    errors = []
    regions = ['EUW','EUNE','NA','BR','OCE','LAN','LAS','TR','RU']
    roles = ['JUNGLE', 'TOP', 'MIDDLE', 'ADC', 'SUPPORT']
    summoner = request.args.get('summoner') #Gets the summoner name from the URL
    region = request.args.get('region')
    role = request.args.get('role')
    matchup = request.args.get('matchup') or None
    if summoner == "" or not summoner:
        errors.append("Summoner field missing")
    if region.upper() not in regions:
        errors.append("Region field missing")
    if role.upper() not in roles:
        errors.append("Role field missing")
    if errors:
        return bad_request(errors)
    pick = models.ChampionPickGenerator(summoner,region,role,matchup) #Creates a variable with the function from models.py
    if pick.api_errors: # if errors in initialisation no need to waste time.
        return bad_request(pick.api_errors)
    pick.run()
    if pick.api_errors:
        return bad_request(pick.api_errors)
    json_string = {'champions':[champion.to_json() for champion in pick.champions]} #Makes a variable for the output as a json  
    return jsonify(json_string)


@api_1_0.route('/details/<champion>/<role>')
def champion_details(champion, role):
    errors = []
    generator = models.ChampionDetailGenerator(champion, role)
    champ_details = generator.get_champion_detail()
    if generator.api_errors:
        return bad_request(generator.api_errors)
    elif not champ_details:
        return bad_request("No data received. Invalid request")
    else:
        return jsonify(champ_details)

