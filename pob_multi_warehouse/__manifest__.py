# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    'name': 'POB:Multi-Warehouse Extension',
    'version': '3.2',
	'sequence': 1,
	'summary':'An extension for Multi-Warehouse support in Prestashop-Odoo Bridge(POB)',
    'category': 'POB',
    'description': """	
    If you are using more than one warehouse on your Odoo.
    This Module helps in maintaining stock between Odoo and prestashop with multi-warehouse functionality on Odoo.
	Basic feature - 
    * Gives an option to choose number of Odoo`s warehous(es) used for your Online shop(PrestaShop) with Prestashop-Odoo Bridge.
    * Depending on the number of warehouses, 
    If choosen 'ALL' -> Product`s Stock will be synchronized with Prestashop is the total number of available Stock on all your Odoo`s Warehouses.
    In this case, you need to choose one default warehouse as well as equivalent Odoo`s Shop in order to select the same warehouse`s S Shop while creating Sales Order on Odoo from PrestaShop.
    If choosen 'SPECIFIC' -> Product`s Stock will be synchronized with Prestashop is the total number of Stock available on that specific Odoo`s Warehouse and equivalent Odoo`s Shop, having same warehouse, is selected while creating Sales Order on Odoo from PrestaShop.  


	NOTE : This module works very well with latest version of prestashop 1.7 and latest version of Odoo 10.0.
    """,
    'author': 'Webkul Software Pvt Ltd.',
    'depends': ['pob'],
    'website': 'http://www.webkul.com',
    'data': ['views/connector_instance.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
