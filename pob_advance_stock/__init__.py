# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from . import models
# from openerp import api,SUPERUSER_ID
# def post_init_create_record(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     employee = env['prestashop.employee'].create({'name':'Select Employee','employee_id':0})
#     conf_ids = env['prestashop.configure'].search(['|',('active','=',True),('active','=',False)])
#     for conf in conf_ids:
#         conf.employee_id = employee.id
#     return True
