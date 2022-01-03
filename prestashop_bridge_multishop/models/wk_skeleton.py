# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields,models,api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.
	from urllib.parse import unquote_plus
	return unquote_plus(text.encode('utf8'))


class WkSkeleton(models.TransientModel):			
	_inherit="wk.skeleton"

	@api.model
	def create_order(self , sale_data):

		""" Create Order on Odoo along with creating Mapping
		@param sale_data: dictionary of Odoo sale.order model fields
		@param context: Standard dictionary with 'ecommerce' key to identify the origin of request and
										e-commerce order ID.
		@return: A dictionary with status, order_id, and status_message"""

		
		ctx = dict(self._context or {})
		# check sale_data for min no of keys presen or not
		order_name, order_id, status, status_message = "", False, True, "Order Successfully Created."
		ecommerce_channel = sale_data.get('ecommerce_channel')
		instance_id = int(ctx.get('instance_id', 0))
		ecommerce_order_id = sale_data.pop('ecommerce_order_id', 0)
		config_data = self.get_default_configuration_data(ecommerce_channel, instance_id)
		sale_data.update(config_data)
		shop_id = sale_data.pop('shop_id', False)
		if shop_id:
			sale_data.update({'wk_shop':int(shop_id)})
			wk_warehouse = self.env['connector.shop.data'].browse(int(shop_id)).warehouse.id
			sale_data.update({'warehouse_id':wk_warehouse})
		try:
			order_obj = self.env['sale.order'].create(sale_data)
			order_id = order_obj.id
			order_name = order_obj.name
			mapping_data = {
				'ecommerce_channel': ecommerce_channel,
				'odoo_order_id': order_id,
				'ecommerce_order_id': ecommerce_order_id,
				'instance_id': instance_id,
				'name': sale_data['origin'],
			}
			self.create_order_mapping(mapping_data)
		except Exception as e:
			status_message = "Error in creating order on Odoo: %s" % str(e)
			_logger.info('#Exception create_order : %r', status_message)
			status = False
		finally:
			return {
				'order_id': order_id,
				'order_name': order_name,
				'status_message': status_message,
				'status': status
			}

