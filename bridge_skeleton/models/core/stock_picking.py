# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


Carrier_Code = [
    ('custom', 'Custom Value'),
    ('dhl', 'DHL (Deprecated)'),
    ('fedex', 'Federal Express'),
    ('ups', 'United Parcel Service'),
    ('usps', 'United States Postal Service'),
    ('dhlint', 'DHL')
]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_code = fields.Selection(
        Carrier_Code,
        string='Ecomm Carrier',
        default="custom",
        help="Ecomm Carrier")
    ecomm_shipment = fields.Char(
        string='Ecomm Shipment',
        help="Contains Ecomm Order Shipment Number (eg. 300000008)")

    def action_done(self):
        self.skeleton_pre_shipment()
        res = super().action_done()
        self.skeleton_post_shipment(res)
        return res

    def skeleton_pre_shipment(self):
        return True

    def skeleton_post_shipment(self, result):
        ctx = dict(self._context or {})
        snippet_obj = self.env['connector.snippet']
        ecomm_cannels = dict(snippet_obj._get_ecomm_extensions()).keys()
        if any(key in ctx for key in ecomm_cannels):
            return True
        for picking in self.filtered(lambda obj : obj.picking_type_code == 'outgoing'):
            sale_order = picking.sale_id
            if sale_order.name == picking.origin and sale_order.ecommerce_channel in ecomm_cannels:
                for ecomm in ecomm_cannels:
                    response = snippet_obj.manual_connector_order_operation('shipment', ecomm, sale_order, picking)
                    picking.ecomm_shipment = response.get('ecomm_shipment', '')


    def ecomm_tracking_sync(self):
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        for picking_obj in self:
            sale_order = picking_obj.sale_id
            ecomm_shipment = picking_obj.ecomm_shipment
            carrier_code = picking_obj.carrier_code
            carrier_tracking_no = picking_obj.carrier_tracking_ref
            if not carrier_tracking_no:
                raise UserError(
                    'Warning! Sorry No Carrier Tracking No. Found!!!')
            elif not carrier_code:
                raise UserError('Warning! Please Select Connector Carrier!!!')
            carrier_title = dict(Carrier_Code)[carrier_code]
            track_vals = {
                "ecom_shipment": ecomm_shipment,
                "track_number": carrier_tracking_no,
                "title": carrier_title,
                "carrier_code": carrier_code
            }
            for ecomm in ecomm_cannels:
                if hasattr(self, '%s_sync_tracking_no' % ecomm):
                    getattr(self, '%s_sync_tracking_no' % ecomm)(picking_obj, sale_order, track_vals)