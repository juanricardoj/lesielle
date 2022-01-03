# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################
import logging

from odoo import api, models
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, *args, **kwargs):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        """
        res = super(StockMove, self)._action_confirm(*args, **kwargs)
        _logger.info("=============_action_confirm============================")
        ctx = dict(self._context or {})
        ctx['stock_operation'] = '_action_confirm'
        _logger.info("===========warehouse id================%r", res)
        res.with_context(ctx).fetch_stock_warehouse()
        return res

    def _action_cancel(self, *args, **kwargs):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        """
        ctx = dict(self._context or {})
        ctx['action_cancel'] = True
        ctx['stock_operation'] = '_action_cancel'
        call_ids = self.filtered(lambda obj: obj.state != 'cancel')
        res = super(StockMove, self)._action_cancel(*args, **kwargs)
        _logger.info("=============r_action_canceles============================")
        if call_ids and res:
            call_ids.with_context(ctx).fetch_stock_warehouse()
        return res

    def _action_done(self, cancel_backorder=False):
        """ Process completly the moves given as ids and if all moves are done, it will finish the picking.
        """
        check = False
        _logger.info("=============read============================%r", self.read(['state']))
        for obj in self:
            if obj.location_id.usage == "inventory" or obj.location_dest_id.usage == "inventory" or (
                    obj.location_id.usage == "supplier" and obj.product_type == 'product'):
                check = True
        res = super(StockMove, self)._action_done(cancel_backorder)
        if check:
            ctx = dict(self._context or {})
            ctx['stock_operation'] = '_action_done'
            self.with_context(ctx).fetch_stock_warehouse()
        return res

    def fetch_stock_warehouse(self):
        ctx = dict(self._context or {})
        if 'stock_from' not in ctx:
            ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
            for data in self:
                odoo_product_id = data.product_id.id
                flag = 1
                if data.origin:
                    sale_objs = data.env['sale.order'].search(
                        [('name', '=', data.origin)])
                    if sale_objs:
                        order_channel = sale_objs[0].ecommerce_channel
                        if order_channel in ecomm_cannels and data.picking_id \
                                and data.picking_id.picking_type_code == 'outgoing':
                            flag = 0
                            _logger.info("==============%r========picking==============",
                                         [data.picking_id, data.picking_id.picking_type_code, order_channel,
                                          ecomm_cannels])
                else:
                    flag = 2  # no origin
                warehouse_id = 0
                if flag == 1:
                    warehouse_id = data.warehouse_id.id
                if flag == 2:
                    location_obj = data.location_dest_id
                    company_id = data.company_id.id
                    warehouse_id = self.check_warehouse_location(
                        location_obj, company_id)  # Receiving Goods
                    if not warehouse_id:
                        location_obj = data.location_id
                        warehouse_id = self.check_warehouse_location(
                            location_obj, company_id)  # Sending Goods
                if warehouse_id:
                    data.check_warehouse(
                        odoo_product_id, warehouse_id, ecomm_cannels)
        return True

    @api.model
    def check_warehouse_location(self, location_obj, company_id):
        warehouse_model = self.env['stock.warehouse']
        while location_obj:
            warehouse_obj = warehouse_model.search([
                ('lot_stock_id', '=', location_obj.id),
                ('company_id', '=', company_id)
            ], limit=1)
            if warehouse_obj:
                return warehouse_obj.id
            location_obj = location_obj.location_id
        return False

    @api.model
    def check_warehouse(self, odoo_product_id, warehouse_id, ecomm_cannels):
        for ecomm in ecomm_cannels:
            if hasattr(self, '%s_stock_update' % ecomm):
                getattr(self, '%s_stock_update' % ecomm)(odoo_product_id, warehouse_id)

        return True


class inventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'draft',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': qty,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
            })]
        }
