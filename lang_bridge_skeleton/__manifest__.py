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
    'name': 'Bridge Skeleton : Multi Language',
    'version': '1.5',
    'sequence': 5,
    'summary':'Bridge Skeleton MultiLanguage Extension',
    'category': 'A Module of WEBKUL Software Pvt Ltd.',
    'description': """	
    Odoo Ecommerce Bridge This Brilliant Module will allow translation feature in that means can have multi-language support.
    
    >>> In order to use this module you have to install our Previous module named as Bridge Skeleton. <<<
    
    This module works very well with latest version of Odoo 13.0.
    """,
    'author': 'Webkul Software Pvt Ltd.',
    'depends': ['bridge_skeleton'],
    'website': 'http://www.webkul.com',
    'data': [
            'security/ir.model.access.csv',                        
            'views/multi_language_view.xml',
            'wizard/synchronization_wizard_view.xml',

            ],
    'installable': True,
    'auto_install': False,
    'active': False,
    'pre_init_hook': 'pre_init_check',
}
