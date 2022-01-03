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
from odoo import tools
from odoo.tools.translate import _
from odoo.addons.pob.models import prestapi
from odoo.exceptions import UserError
from odoo.addons.pob.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError
import logging
_logger = logging.getLogger(__name__)




############## Inherited PrestaShop classes #################
class ConnectorInstance(models.Model):			
    _inherit = "connector.instance"

    @api.model
    def _update_list(self):
        try:
            return_list = []
            config_ids = self
            if not config_ids:
                config_ids = self.search([('active','=',True)])
            if config_ids:
                for config_id in config_ids:
                    url=config_id[0].user
                    key=config_id[0].pwd
                    try:
                        prestashop = PrestaShopWebServiceDict(url,key)
                    except PrestaShopWebServiceError as e:
                        raise UserError(_('Error %s')%str(e))
                    if prestashop:
                        employees = prestashop.get('employees',options={'display': '[id,firstname,lastname]','filter[active]': '1'})
                        if 'employees' in employees:
                            employees = employees['employees']
                        if type(employees['employee'])==list:
                            for row in employees['employee']:
                                return_list.append((row['id'],row['firstname']+row['lastname']))
                        else:
                            return_list.append((employees['employee']['id'],
                            employees['employee']['firstname']+employees['employee']['lastname']))
            return return_list
        except:
            return []

    employee_id  = fields.Selection(_update_list, 'Prestashop Employee', default=_update_list)
    advance_stock = fields.Boolean(
        'Advance Stock',
        default=False,
        )


    def refresh_list(self):
        view_ref = self.env['ir.model.data'].get_object_reference('bridge_skeleton', 'connector_instance_form')
        view_id = view_ref and view_ref[1] or False,
        return {
                'type': 'ir.actions.act_window',
                'name': 'Ecomm Configuration',
                'res_model': 'connector.instance',
                'res_id': self._ids[0],
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'current',
                'nodestroy': True,
                }