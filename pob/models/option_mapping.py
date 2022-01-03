# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class ConnectorOptionMapping(models.Model):
    _inherit = "connector.option.mapping"

    ecomm_attr_id = fields.Integer(string='Ecomm Attribute Id')
    odoo_attr_id = fields.Integer(string='Odoo Attribute Id')