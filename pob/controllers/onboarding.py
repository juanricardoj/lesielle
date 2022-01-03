# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   "License URL : <https://store.webkul.com/license.html/>"
#
##########################################################################

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class OnboardingController(http.Controller):

    @http.route('/pob/pob_dashboard_onboarding', auth='user', type='json')
    def pob_dashboard_onboarding(self):
        connectInfo = request.env['pob.dashboard'].get_connection_info()
        return {
            'html': request.env.ref('pob.pob_dashboard_onboarding_panel').render({
                'connrecs': connectInfo})
        }
