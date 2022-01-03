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



############## Inherited PrestaShop classes #################
class ConnectorSnippet(models.TransientModel):			
	_inherit = "connector.snippet"

	@api.model
	def create_shop(self, data):
		company_id = self.env['res.company']._company_default_get('connector.snippet')
		warehouse_id = self.env['stock.warehouse'].search([('company_id','=',company_id.id)])[0]
		shop = {
			   'name': data.get('name'),
			   'warehouse':warehouse_id.id,
			   'instance_id' : self._context.get('instance_id', False)
			  	}
		shop_id = self.env['connector.shop.data'].create(shop)
		return shop_id.id