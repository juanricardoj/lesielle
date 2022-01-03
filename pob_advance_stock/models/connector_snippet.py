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


class ConnectorSnippet(models.TransientModel):
    _inherit = 'connector.snippet'


    @api.model
    def update_quantity(self, data):
        """ Changes the Product Quantity by making a Physical Inventory through any service like xmlrpc.
        @param data: Dictionary of product_id and new_quantity
        @param context: A standard dictionary
        @return: True
        """
        ctx = dict(self._context or {})
        prod_obj_pool = self.env['product.product']
        prod_obj = prod_obj_pool.with_context(ctx).browse(data.get('product_id'))
        if 'instance_id' in ctx:
            if 'location' in data:
                location_id = int(data.get('location'))
            else:
                connection_obj  = self.env['connector.instance'].browse(ctx.get('instance_id'))
                location_objs   = connection_obj.warehouse_id if connection_obj.active else self.env['stock.warehouse'].search([], limit=1)
                location_id     = location_objs.lot_stock_id.id
            if location_id:
                th_qty = prod_obj.qty_available
                if 'flag' in data:
                    th_qty = prod_obj.with_context({'location' : location_id}).qty_available
                    if data['flag']:
                        data['new_quantity'] = int(data.get('new_quantity')) + th_qty
                    else:
                        data['new_quantity'] =  th_qty - int(data.get('new_quantity'))

                ctx['inventory_mode'] = True
                self.env['stock.quant'].with_context(ctx).create({
                            'product_id': data.get('product_id'),
                            'location_id':location_id,
                            'inventory_quantity': int(data.get('new_quantity', 0)),
                })
            return True
        else:
            return "Sorry, Default Stock Location not found!!!"
        return True