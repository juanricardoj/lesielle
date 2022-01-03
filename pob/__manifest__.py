#!/usr/bin/env python
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
    'name': 'POB - PrestaShop-Odoo Bridge',
    'version': '6.1.0',
    'author': 'Webkul Software Pvt. Ltd.',
    'summary': 'Bi-directional synchronization with PrestaShop',
    'description': """
POB - PrestaShop-Odoo Bridge
==============================
This module establish bridge between your Odoo and PrestaShop and allows bi-directional synchronization of your data between them.

NOTE: You need to install a corresponding 'Prestashop-Odoo Bridge' plugin on your prestashop too,
in order to work this module perfectly.

Key Features
------------
* export/update "all" or "selected" or "multi-selected" products,with images, from Odoo to Prestashop with a single click.
* export/update "all" or "selected" or "multi-selected" categories from Odoo to Prestashop with a single click.
* maintain order`s statuses with corressponding orders on prestashop.(if the order is created from prestashop)
* export/update "all" or "selected" or "multi-selected" categories from Odoo to Prestashop with a single click.

Dashboard / Reports:
------------------------------------------------------
* Orders created from Prestashop on specific date-range

For any doubt or query email us at support@webkul.com or raise a Ticket on http://webkul.com/ticket/
    """,
    'website': 'http://www.webkul.com',
    'images': [],
    'depends': ['bridge_skeleton' ,'variant_price_extra'],
    'category': 'POB',
    'sequence': 1,
    'data': [
        'views/connector_instance.xml',
        'views/option_mapping.xml',
        'views/connector_product_mapping.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    "external_dependencies":  {'python': ['requests']},
}
