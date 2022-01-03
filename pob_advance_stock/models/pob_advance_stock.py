# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
#
##############################################################################




from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
class WkAdvanceStock(models.Model):
    _name = 'wk.advance.stock'

    currency_id         = fields.Integer('Prestashop Currency')
    presta_warehouse_id = fields.Integer('Prestashop Warehouse')
    location            = fields.Many2one('stock.location','Location')

class ConnectorShopData(models.Model):
    _inherit = 'connector.shop.data'

    route_id = fields.Many2one('stock.location.route', 'Stock Location Route')
    

