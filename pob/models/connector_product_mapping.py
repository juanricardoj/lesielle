# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class ConnectorProductMapping(models.Model):
    _inherit = "connector.product.mapping"

    ecomm_combination_id = fields.Integer(string='Ecomm Combination Id')
    odoo_tmpl_id = fields.Integer(string='Odoo Template Id')