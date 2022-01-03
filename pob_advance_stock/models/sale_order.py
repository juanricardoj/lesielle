 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

from odoo import fields,models,api
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        saleOrder = self.env['sale.order']
        if vals.get('order_id',False):
            sale_id = saleOrder.browse(vals['order_id'])
            if sale_id.wk_shop and sale_id.wk_shop.route_id:
                vals['route_id'] = sale_id.wk_shop.route_id.id
        return super(SaleOrderLine, self).create(vals)
        