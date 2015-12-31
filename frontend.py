#!/usr/bin/python3
# This file is part of waymarkedtrails.org
# Copyright (C) 2015 Sarah Hoffmann
#
# This is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import sys
from os.path import join as os_join
from os import environ as os_environ
import cherrypy

import config.defaults
import api.tools

api.tools.SAEnginePlugin(cherrypy.engine).subscribe()
cherrypy.tools.db = api.tools.SATool()

from api.routes import RoutesApi
from frontend.help import Helppages

@cherrypy.tools.I18nTool()
class Trails(object):

    def __init__(self):
        self.api = RoutesApi()
        self.help = Helppages()

    @cherrypy.expose
    def index(self, **params):
        return cherrypy.request.templates.get_template('index.html').render(
                                     g=cherrypy.request.app.config.get('Global'),
                                     l=cherrypy.request.app.config.get('Site'))


class _MapDBOption:
    no_engine = True

def setup_site(confname, script_name=''):
    globalconf = {}
    for var in dir(sys.modules['config.defaults']):
        if var.isupper():
            globalconf[var] = getattr(sys.modules['config.defaults'], var)

    site_cfg = {}
    try:
        __import__('config.sites.' + confname)
        site_cfg = getattr(sys.modules['config.sites.' + confname], 'SITE', {})
    except ImportError:
        print("Missing config for site '%s'. Skipping." % site)
        raise

    app = cherrypy.tree.mount(Trails(), script_name + '/')

    os_environ['ROUTEMAPDB_CONF_MODULE'] = 'maps.%s' % confname
    from db.routes import DB
    app.config['DB'] = { 'map' : DB(_MapDBOption()) }

    # add the options from config.defaults
    app.config['Global'] = globalconf
    app.config['Global']['BASENAME'] = confname
    app.config['Site'] = site_cfg

    # now disable trailing slash
    cherrypy.config.update({'tools.trailing_slash.on': False })


def application(environ, start_response):
    """ Handler for WSGI appications."""
    setup_site(environ['WMT_CONFIG'], script_name=environ['SCRIPT_NAME'])
    globals()['application'] = cherrypy.tree
    return cherrypy.tree(environ, start_response)

if __name__ == '__main__':
    setup_site(os_environ['WMT_CONFIG'])
    cherrypy.config.update({'server.socket_host' : '0.0.0.0'})
    cherrypy.engine.start()
    cherrypy.engine.block()