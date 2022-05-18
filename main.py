#!/usr/bin/python3
"""
Copyright (c) 2012 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
__author__ = "David Brown <davibrow@cisco.com>"
__contributors__ = []
__copyright__ = "Copyright (c) 2012 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import flask

from vmanage_api import rest_api_lib
from flask import Flask, request, make_response, render_template, redirect, url_for, session
from markupsafe import Markup
from pandas import read_csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'any random string'

vedges = ['']

###########################################################################
# Gets vManage variables from cookie and returns a vManage login object
###########################################################################
def login():

    vmanage_name = request.cookies.get('vmanage')
    vmanage_user = request.cookies.get('userid')
    vmanage_pass = request.cookies.get('password')
    vmanage = rest_api_lib(vmanage_name, vmanage_user, vmanage_pass)

    return vmanage


###########################################################################
#  Prompt user to set vManage settings
###########################################################################
@app.route('/')
def get_vmanage():
    vmanage = request.cookies.get('vmanage')
    userid = request.cookies.get('userid')
    password = request.cookies.get('password')
    if vmanage is None:
        vmanage = userid = password = 'not set'
    return render_template('get_settings.html', vmanage=vmanage, userid=userid, password=password,
                           secret='*****' + password[-2:])


###########################################################################
#  Read and save settings
###########################################################################
@app.route('/savesettings')
def save_vmanage():

    resp = make_response(redirect(url_for('get_device')))
    for arg in request.args:
        resp.set_cookie(arg, request.args.get(arg), secure=True, httponly=True)
    return resp


@app.route('/device')
def get_device():
    try:
        vmanage = login()
    # Problems logging into vManage should be caught here...
    except Exception as err:
        return render_template('error.html', err=err)
    devices = vmanage.get_request('device')
    vmanage.logout()
    device_list = ''
    for device in devices['data']:
        if (device['reachability'] == 'reachable') and (device['personality'] == 'vedge'):
            device_list += f'<option value="{device["deviceId"]}|{device["version"]}">{device["host-name"]:20}{device["deviceId"]}</option>\n'
    return render_template('get_device.html', vmanage=request.cookies.get('vmanage'), device_list=Markup(device_list))


###########################################################################
#  Prompts user for route lookup values
###########################################################################
@app.route('/iproute')
def get_target():

    args = request.args.get('device')
    [device, version] = args.split('|')

    session['version'] = version.split('.')[0]
    try:
        vmanage = login()
    # Problems logging into vManage should be caught here...
    except Exception as err:
        return render_template('error.html', err=err)
    interfaces = vmanage.get_request(f'device/interface/vpn?deviceId={device}')['data']
    vpns = []
    for interface in interfaces:
        if interface['vpnId'] not in vpns:
            vpns.append(interface['vpnId'])
    vmanage.logout()
    vpn_list = ''
    vpns.sort()
    for vpn in vpns:
        vpn_list += f'<option value="{str(vpn)}">{str(vpn)}</option>\n'
    return render_template('route_search.html', vmanage=request.cookies.get('vmanage'), device=device,
                           vpn_list=Markup(vpn_list))


###########################################################################
# Looks up the longest match route and returns a web page
###########################################################################
@app.route('/result')
def list_routes():

    masks = [0, 128, 192, 224, 240, 248, 252, 254, 255]

    vpn = request.args.get('vpn')
    device = request.args.get('device')
    prefix = request.args.get('prefix')
    version = session.get('version')

    # Pull Route Table
    vmanage = login()
    if version == '17':
        url = f'device/ip/ipRoutes?routing-instance-name={vpn}&deviceId={device}'
        target = 'route-destination-prefix'
    else:
        url = f'device/ip/routetable?vpn-id={vpn}&deviceId={device}'
        target = 'prefix'
    response = vmanage.get_request(url)
    vmanage.logout()

    # Generate response columns headers
    header = []
    for item in response['header']['columns']:
        header.append(item['title'])
    result = ','.join(header) + '\n'

    # Generate list of all networks in query
    [network, prefix_length] = prefix.split('/')
    octets = network.split('.')
    new_octets = [0, 0, 0, 0]
    networks = []
    for length in range(int(prefix_length), -1, -1):
        for octet in range(4):
            bits = (length >= octet*8) * (8 * (length >= (octet+1)*8) + (length-octet*8) * (length < (octet+1)*8))
            new_octets[octet] = str(masks[bits] & int(octets[octet]))
        if (new_octets == ['0', '0', '0', '0']) and (length > 0):
            continue
        else:
            new_prefix = f"{'.'.join(new_octets)}/{length}"
        networks.append(new_prefix)

    # Generate CSV of matching results
    paths = []
    for route in response['data']:
        if route[target] in networks:
            entry = []
            for prop in response['header']['columns']:
                try:
                    value = route[prop['property']]
                    if prop['property'] == 'lastupdated':
                        time = datetime.fromtimestamp(int(value/1000))
                        value = f'{time.hour}:{time.minute} {time.month}/{time.day}/{time.year}'
                    entry.append(str(value))
                except KeyError:
                    entry.append('N/A')
            paths.append(entry)
    paths.reverse()
    for route in paths:
        result += ','.join(route) + '\n'

    #Generate Webpage
    result_html = read_csv(StringIO(result), keep_default_na=False).to_html()
    page = f'<a href="/iproute?device={device}|{version}">Search another network on this device</a><br>' \
           f'<html><body><a href="/device">Choose another device</a><br><br>'
    page += result_html
    page += '</body></html>'

    return Markup(page)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]
