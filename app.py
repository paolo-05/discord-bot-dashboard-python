import asyncio
from os import stat

import requests
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_cors import CORS, cross_origin

import sql
from config import BOT_API_URL, CLIENT_ID, LOGIN_URL
import utils

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = "this_is_a_secret"


@app.route('/')
def homepage():
    r = requests.get(f'{BOT_API_URL}/status')
    guilds = r.json()['guilds']
    ping = r.json()['ping']
    users = r.json()['users']

    return render_template('index.html', CLIENT_ID=CLIENT_ID, LOGIN_URL=LOGIN_URL, guilds=guilds, ping=ping, users=users)


@app.route('/oauth/discord')
def oauth():
    token = utils.get_token(request.args.get('code'))
    session['token'] = token
    return redirect('/dashboard')


@app.route('/dashboard')
def dashboard():
    if 'token' not in session:
        return redirect(LOGIN_URL)
    user_guilds = utils.get_user_guilds(session.get('token'))
    bot_guilds = utils.get_bot_guilds()
    mutual_guilds = utils.get_mutual_guilds(user_guilds, bot_guilds)
    print(mutual_guilds)
    return render_template('dashboard.html', mutual_guilds=mutual_guilds, user_guilds=user_guilds, n_guilds=len(mutual_guilds))


@app.route('/guild/<guild_id>')
def guild(guild_id: int):

    if 'token' not in session:
        return redirect(LOGIN_URL)
    guild_info = utils.get_guild_data(guild_id)
    if not guild_info:
        return redirect(f'https://discord.com/api/oauth2/authorize?client_id=840300480382894080&permissions=8&redirect_uri=https%3A%2F%2Fxgnbot.herokuapp.com%2Foauth%2Fdiscord&response_type=code&guild_id={guild_id}&scope=identify%20guilds%20bot%20applications.commands')

    r = requests.get(f'{BOT_API_URL}/status')
    guilds = r.json()['guilds']
    ping = r.json()['ping']
    users = r.json()['users']

    data = {
        'guild_id': guild_id,
    }

    r1 = requests.post(f'{BOT_API_URL}/guilds', json=data)
    json = r1.json()['guild']
    people = json['person_count']
    bot_count = json['bot_count']
    boost = json['boost']
    tc = json['text_channels']
    voice_c = json['voice_channels']

    token = session['token']
    user = utils.get_user_info(token)
    text_channels = utils.get_guild_channels(guild_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    prefix, welcome_enabled, welcome_channel, welcome_message, leave_enabled, leave_message, leave_channel, level_up_enabled, level_message, level_channel, log_enabled, log_channel = loop.run_until_complete(
        sql.get_config(guild_id))

    loop.close()

    return render_template(
        'guild.html',
        guilds=guilds, ping=ping, users=users, text_channels=text_channels, user=user,
        people=people, bot_count=bot_count, boost=boost, tc=tc, voice_c=voice_c, members=people+bot_count,
        guild=guild_info,
        prefix=prefix,
        welcome_enabled=welcome_enabled,
        welcome_channel=welcome_channel,
        welcome_message=welcome_message,
        leave_enabled=leave_enabled,
        leave_message=leave_message,
        leave_channel=leave_channel,
        log_enabled=log_enabled,
        log_channel=log_channel,
        level_up_enabled=level_up_enabled,
        level_channel=level_channel,
        level_message=level_message,
    )


@app.route('/leaderboard/<guild_id>')
def leaderboard(guild_id: int):

    data = {
        'guild_id': guild_id,
    }
    r1 = requests.post(f'{BOT_API_URL}/guilds', json=data)
    people = r1.json()["guild"]['person_count']
    bot_count = r1.json()["guild"]['bot_count']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    prefix, welcome_enabled, welcome_channel, welcome_message, leave_enabled, leave_message, leave_channel, level_up_enabled, level_message, level_channel, log_enabled, log_channel = loop.run_until_complete(
        sql.get_config(guild_id))

    leaderboard_users = []
    r = requests.post(f'{BOT_API_URL}/leaderboard', json=data)
    print(r.json())
    json = r.json()['leaderboard']
    counter = 0
    for i in json:
        user = utils.get_user_info_by_id(i['user'])
        xp = i['exp']
        lvl = i['lvl']
        counter += 1
        leaderboard_users.append(
            {'user': user, 'xp': xp, 'lvl': lvl, 'counter': counter})

    guild_info = utils.get_guild_data(guild_id)

    return render_template(
        'leaderboard.html',
        level_up_enabled=level_up_enabled,
        guild=guild_info,
        people=people,
        bot_count=bot_count,
        members=people+bot_count,
        leaderboard_users=leaderboard_users)


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


###### API ROUTES ######

@app.route('/api/status', methods=['GET', 'POST'])
@cross_origin()
def api_status():
    return jsonify(status=200)


@app.route('/api/enablewelcome', methods=["POST"])
@cross_origin()
def enable_welcome():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']
    message = ''
    channel_id = 0

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.welcome_event(
        guild_id, message, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/changewelcome', methods=["POST"])
@cross_origin()
def change_welcome():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']
    if json['message'] is not None:
        message = json['message']
    else:
        message = 'hello'

    if json['channel_id'] is not None:
        channel_id = json['channel_id']
    else:
        channel_id = 12423423432

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.welcome_event(
        guild_id, message, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/enableleave', methods=["POST"])
@cross_origin()
def enable_leave():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']
    message = ''
    channel_id = 0

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.leave_event(
        guild_id, message, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/changeleave', methods=["POST"])
@cross_origin()
def change_leave():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']
    if json['message'] is not None:
        message = json['message']
    else:
        message = 'hello'

    if json['channel_id'] is not None:
        channel_id = json['channel_id']
    else:
        channel_id = 12423423432

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.leave_event(
        guild_id, message, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/enableleveling', methods=["POST"])
@cross_origin()
def enable_leveling():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']
    message = ''
    channel_id = 0

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.level_system(
        guild_id, message, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/changeleveling', methods=["POST"])
@cross_origin()
def change_leveling():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']

    message = json['message']

    channel_id = json['channel_id']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.level_system(
        guild_id, message, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/change_prefix', methods=["POST"])
@cross_origin()
def change_prefix():
    json = request.get_json('guild_id')

    prefix = json['prefix']
    guild_id = json['guild_id']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.change_prefix(prefix, guild_id))

    return jsonify(status=200)


@app.route('/api/enablelog', methods=["POST"])
@cross_origin()
def enable_log():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']
    channel_id = 0

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.log_system(
        guild_id, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/changelog', methods=["POST"])
@cross_origin()
def change_log():
    json = request.get_json('guild_id')

    guild_id = json['guild_id']

    channel_id = json['channel_id']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.log_system(
        guild_id, int(channel_id)))

    return jsonify(status=200)


@app.route('/api/disable', methods=['POST'])
@cross_origin()
def disable():
    json = request.get_json('guild_id')
    guild_id = json['guild_id']
    action = json['action']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(sql.disable_(guild_id, action))

    return jsonify(status=200)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# if __name__ == '__main__':
#    app.run(debug=True)
