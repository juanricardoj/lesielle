#!/usr/bin/env python
# -*- coding: utf-8 -*-
##################################################################################
#                                                                                #
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)#
#																				 #
##################################################################################

from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.addons.pob.models import prestapi
from odoo.addons.pob.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError
# from . import prestapi
# from .prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
import logging
_logger = logging.getLogger(__name__)

def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.
	from urllib import unquote_plus
	return unquote_plus(text.encode('utf8'))
################## .............prestashop-odoo stock.............##################

# Overriding this class in order to handle Stock Management b/w Odoo n PrestaShop.
class StockMove(models.Model):
	_inherit="stock.move"


	#@api.multi
	def _action_confirm(self,merge=True,merge_into=False):
		""" Confirms stock move or put it in waiting if it's linked to another move.
		"""
		res = super(StockMove, self)._action_confirm()
		_logger.info("============_action_confirm============")
		pob_conf = self.env['prestashop.configure'].search([('active', '=', True)])
		if pob_conf.stock_type == "onhand":
			ctx = dict(self._context or {})
			self.with_context(ctx).pob_fetch_stock()
		return res

	#@api.multi
	def _action_cancel(self):
		""" Confirms stock move or put it in waiting if it's linked to another move.
		"""
		ctx = dict(self._context or {})
		ctx['action_cancel'] = True
		pob_conf = self.env['prestashop.configure'].search([('active', '=', True)])
		_logger.info("============_action_cancel============")
		check = False
		for obj in self:
			if obj.state == "cancel":
				check = True
		res = super(StockMove, self)._action_cancel()
		if pob_conf.stock_type == "forecast" and not check:
			self.with_context(ctx).pob_fetch_stock()
		return res


	#@api.multi
	def _action_done(self):
		""" Makes the move done and if all moves are done, it will finish the picking.
		@return:
		"""
		context = self.env.context.copy() or {}
		moves_todo = super(StockMove, self)._action_done()
		todo = [move for move in self if move.state == "draft"]
		ids = self
		if todo:
			ids = todo._action_confirm()
		if 'prestashop' not in context :
			self.pob_fetch_stock(ids)
		return moves_todo


	#@api.multi
	def pob_fetch_stock(self, ids=None):
		if ids is None:
			ids = self
		context = self.env.context.copy() or {}
		check_out,check_in = [False, False]
		product_qty = 0
		pob_conf = self.env['prestashop.configure'].search([('active', '=', True)])
		if pob_conf:
			pob_location = pob_conf[0].pob_default_stock_location.id
		else:
			pob_location = -1
		for id in ids:
			data = self.browse(id.id)
			erp_product_id = data.product_id.id
			flag = 2 # means there is some origin.
			if data.origin != False:
				# Check if origin is 'Sale' and channel is 'prestashop',no need to update quantity.
				sale_id = self.env['sale.order'].search([('name', '=', data.origin)])
				if sale_id:
					get_channel = sale_id[0].ecommerce_channel
					if get_channel == 'prestashop':
						flag = 0 # no need to update quantity.
			else:
				flag = 2 # no origin.
			if flag == 2:
				pob_conf = self.env['prestashop.configure'].search([('active', '=', True)])
				if pob_conf:
					pob_location = pob_conf[0].pob_default_stock_location.id
				else:
					pob_location = -1
				if data.location_dest_id.id == pob_location:
					check_in = True
				elif data.location_id.id == pob_location:
					check_out = True
			if check_in:
				product_qty = int(data.product_qty)
			if check_out:
				product_qty = int(-data.product_qty)
			if check_in or check_out:
				self.synch_quantity(erp_product_id, product_qty, pob_conf)
		return True

	# Extra function to update quantity(s) of product to prestashop`s end.
	#@api.multi
	def synch_quantity(self, erp_product_id, product_qty, config_ids):
		response = self.update_quantity(erp_product_id, product_qty, config_ids[0])
		if response[0]==1:
			return True

	# Function to update quantity of products to prestashop`s end.
	#@api.multi
	def update_quantity(self, erp_product_id, quantity, config_id):
		check_mapping=self.env['prestashop.product'].search([('erp_product_id', '=', erp_product_id)])
		if check_mapping:
			presta_product_id = check_mapping[0].presta_product_id
			presta_product_attribute_id = check_mapping[0].presta_product_attr_id
			if config_id:
				url = config_id.api_url
				key = config_id.api_key
				try:
					prestashop = PrestaShopWebServiceDict(url, key)
				except Exception as e:
					return [0,' Error in connection',check_mapping[0]]
				try:
					stock_search = prestashop.get('stock_availables',options={'filter[id_product]':presta_product_id,'filter[id_product_attribute]':presta_product_attribute_id})
				except Exception as e:
					return [0,' Unable to search given stock id', check_mapping[0]]
				if type(stock_search['stock_availables']) == dict:
					if isinstance(stock_search['stock_availables']['stock_available'],list):
						stock_id = stock_search['stock_availables']['stock_available'][0]['attrs']['id']
					else:
						stock_id = stock_search['stock_availables']['stock_available']['attrs']['id']
					try:
						stock_data = prestashop.get('stock_availables', stock_id)
					except Exception as e:
						return [0,' Error in Updating Quantity,can`t get stock_available data.',check_mapping[0]]
					product = self.env['product.product'].browse(erp_product_id)
					if config_id.stock_type == 'onhand':
						quantity = product.with_context({'location' : config_id.pob_default_stock_location.id}).qty_available
					else:
						quantity = product.with_context({'location' : config_id.pob_default_stock_location.id}).virtual_available
					if type(quantity) == str:
						quantity = quantity.split('.')[0]
					if type(quantity) == float:
						quantity = int(quantity)
					stock_data['stock_available']['quantity'] = int(quantity)
					try:
						up = prestashop.edit('stock_availables', stock_id, stock_data)
					except:
						pass
					return [1,'']
				else:
					return [0,' No stock`s entry found in prestashop for given combination (Product id:%s ; Attribute id:%s)'%(str(presta_product_id),str(presta_product_attribute_id)),check_mapping[0]]
		else:
			return [1,'']
