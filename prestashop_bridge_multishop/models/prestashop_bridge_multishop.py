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

############## Inherited PrestaShop classes #################
class ForceDone(models.Model):			
	_inherit="force.done"

	@api.multi
	def create_shop(self, data):
		company_id=self.env['res.company']._company_default_get('force.done')
		warehouse_id=self.env['stock.warehouse'].search([('company_id','=',company_id.id)])[0]
		shop = {
			   'name': data.get('name'),
			   'warehouse':warehouse_id.id
			  	}
		shop_id=self.env['wk.sale.shop'].create(shop)
		return shop_id.id

class WkSkeleton(models.TransientModel):			
	_inherit="wk.skeleton"

	@api.model
	def create_order(self,order_data):
		# check order_data for min no of keys presen or not
		order_name,order_id,status,status_message = "",False,True,"Order Successfully Created."
		sale_data = {
		'partner_id'			:order_data['partner_id'], # Customer
		'partner_invoice_id'	:order_data['partner_invoice_id'], # Invoice Address
		'partner_shipping_id'	:order_data['partner_shipping_id'], # Delivery Address
		'pricelist_id'			:order_data['pricelist_id'], # Pricelist
		'origin'				:order_data['ecommerce_order_ref'], # eCommerce Order Ref
		'ecommerce_channel'		:order_data['ecommerce_channel'] # eCommerce Channel
		}
		if 'date_order' in order_data: # Order Date
			sale_data['date_order'] = order_data['date_order']
		if 'note' in order_data: # Terms and conditions
			sale_data['note'] = order_data['note']
		if 'payment_method_id' in order_data: # Payment Method
			sale_data['payment_method'] = order_data['payment_method_id']
		if 'carrier_id' in order_data: # Carrier ID
			sale_data['carrier_id'] = order_data['carrier_id']
		if order_data.get('shop_id'):
				sale_data.update({'wk_shop':order_data['shop_id']})
				wk_warehouse = self.env['wk.sale.shop'].browse(int(order_data['shop_id'])).warehouse.id
				sale_data.update({'warehouse_id':wk_warehouse})
		config_data = self.get_default_configuration_data(order_data['ecommerce_channel'])
		sale_data.update(config_data)
		# if config_data.has_key('team_id'): # Sales Team
		# 	sale_data['team_id'] = config_data['team_id']
		# if config_data.has_key('payment_term_id'): # Payment Term
		# 	sale_data['payment_term_id'] = config_data['payment_term_id']
		# if config_data.has_key('user_id'): # Salesperson
		# 	sale_data['user_id'] = config_data['user_id']
		try:
			order_id = self.env['sale.order'].create(sale_data)
			order_name = order_id.name
			self.create_order_mapping({
				'ecommerce_channel':order_data['ecommerce_channel'],
				'erp_order_id':order_id.id,
				'ecommerce_order_id':order_data['ecommerce_order_id'],
				'name':order_data['ecommerce_order_ref'],
				})
		except Exception as e:
			status_message = "Error in creating order on Odoo: %s"%str(e)
			status = False
		finally:
			return {
				'order_id': order_id.id,
				'order_name': order_name,
				'status_message': status_message,
				'status': status
			}

class WkSaleShop(models.Model):	
	_name = 'wk.sale.shop'

	# _columns = {
	name =  fields.Char(string='Shop Name',size=100)
	warehouse = fields.Many2one('stock.warehouse', string='Warehouse')
	stock_location = fields.Many2one('stock.location',related='warehouse.lot_stock_id',string="Stock Location")

	# }
WkSaleShop()	

class SaleOrder(models.Model):
	_inherit = "sale.order"

	# _columns = {     
	wk_shop = fields.Many2one('wk.sale.shop', string='Odoo Shop')
		# }

SaleOrder()