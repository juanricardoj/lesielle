# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
#
##############################################################################

from odoo import api,fields, models
import logging
_logger = logging.getLogger(__name__)

class LanguageMapping(models.Model):
    _name = "connector.language.mapping"
    _description = "Language Mapping"

    name = fields.Char(string='Language Code', size=64)
    odoo_lang_id = fields.Integer(string='Odoo lang Id')
    ecommerce_lang_id = fields.Char(string='Ecommerce lang Id')
    instance_id = fields.Many2one(
        'connector.instance',
        string='Ecommerce Instance')
    ecommerce_channel = fields.Selection(
        related="instance_id.ecomm_type", 
        string="eCommerce Channel", store=True)


    _sql_constraints = [
        ('lang_mapping_unique', 'unique(odoo_lang_id,ecommerce_lang_id,instance_id)', "Combination Of Odoo lang ID,Ecommerce Lang ID and Instance ID should be Unique !"),
    ]
    
    @api.model
    def create_lang_mapping(self, values):
        code = ""
        status = False
        odoo_lang_id = values.get('odoo_lang_id', False)
        if odoo_lang_id:
            resp = self.env['res.lang'].browse(int(odoo_lang_id))
            if resp:
                code = resp.code
                values['name'] = code
                created = self.create(values)
                if created:
                    status = True
        return {
            'status':status,
            'code':code
        }
