# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api, fields, models, _

############## Override classes #################

class WkSkeleton(models.TransientModel):
    _inherit = 'wk.skeleton'


    def get_prestashop_configuration_data(self ,connecntionObj):
        return{
            'warehouse_id' : connecntionObj.warehouse_id.id
            }

    @api.model
    def add_tracking_number(self, data):
        order_name=self.env['sale.order'].browse(data['order_id']).name_get()
        pick_id = self.env['stock.picking'].search([('origin','=',order_name[0][1])])
        if pick_id:
            pick_id[0].write({'carrier_tracking_ref':data['track_no']})
        return True
    
    @api.model
    def get_ecomm_href(self, getcommtype=False):
        href_list = super().get_ecomm_href(getcommtype)
        if getcommtype=='prestashop':
            href_list = {
            'user_guide':'https://store.webkul.com/Prestashop-Openerp-Connector.html',
            'rate_review':'https://store.webkul.com/Prestashop-Openerp-Connector.html#tabreviews',
            'extension':'https://store.webkul.com/Odoo/Connector-s-Extensions.html',
            'name' : 'PRESTASHOP',
            'short_form' : 'Pob',
            'img_link' : '/pob/static/src/img/logo.png'
            }
        return href_list