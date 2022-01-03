# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,models,fields
from odoo import tools
from odoo.exceptions import UserError,Warning
import logging
from odoo.tools.translate import _
from odoo.addons.pob.models import prestapi
from odoo.addons.pob.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError
from odoo.tools.translate import translate
import traceback,sys
import datetime
import urllib3

_logger = logging.getLogger(__name__)
try:
	from odoo.loglevels import ustr as pob_decode
except:
	from odoo.tools.misc import ustr as pob_decode


def _decode(name):
	# name = name.translate(None,'=+')
	name = urllib3.parse.unquote(name)
	#DB is corrupted with utf8 and latin1 chars.
	decoded_name = name
	if isinstance(name, unicode):
		try:
			decoded_name = name.encode('utf8')
		except:
			decoded_name = name
	else:
		try:
			decoded_name = unicode(name, 'utf8')
		except:
			try:
				decoded_name = unicode(name, 'latin1').encode('utf8')
			except:
				decoded_name = name
	return decoded_name

def _unescape(text):
    	##
	# Replaces all HTML entities from a text string with plain utf8 string.
	#
	# @param text The HTML source text.
	# @return The plain text, as a Unicode string, if necessary.
	import re, html.entities as htmlentitydefs
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return chr(int(text[3:-1], 16))
				else:
					return chr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = chr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text # leave as is
	return re.sub("&#?\w+;", fixup, text)
################## .............prestashop_language .............##################
class PrestashopLanguage(models.Model):			
	_name="prestashop.language"
	
	def _get_list(self):
		_logger.info("======get_list=========>")
		try:
			return_list=[]
			config_id=self.env['prestashop.configure'].search([('active','=',True)])
			if not config_id:
				raise UserError(_("Connection needs one Active Configuration setting."))
			if len(config_id)>1:
				raise UserError(_("Sorry, only one Active Configuration setting is allowed."))
			else:
				obj=config_id[0]
				url=obj.api_url
				key=obj.api_key
				try:
					prestashop = PrestaShopWebServiceDict(url,key)
					_logger.info("===============>%r",prestashop)
				except PrestaShopWebServiceError as e:
					raise UserError(_('Error %s')%str(e))
				if prestashop:
					languages_data=prestashop.get('languages',options={'display': '[id,name]','filter[active]': '1'})	
					for row in languages_data['languages']['language']:
						return_list.append((row['id'],row['name']))
					return return_list
		except:
			return [('-1','Sorry, Data Not Available')]
		
	@api.multi	
	def addto_prestashop_merge(self,data):
		error_msg=''
		try:
			config_id=self.env['prestashop.configure'].search([('active','=',True)])			
			if not config_id:
				raise Warning("Connection needs one Active Configuration setting.")
			if len(config_id)>1:
				raise Warning("Sorry, only one Active Configuration setting is allowed.")
			else:
				obj=config_id[0]
				url=obj.api_url
				key=obj.api_key

				prestashop = PrestaShopWebServiceDict(url,key)
				if prestashop:
					try:
						# _logger.info('-------------------wk---------------resource--data------------>%r',resource_data)
						resource_data = prestashop.get('erp_language_merges', options={'schema': 'blank'})
					except Exception as e:
						return [0,' Error in Creating blank schema for resource -->.'+str(e)]
					resource_data['erp_language_merge'].update({
					'erp_language_id':data['erp_id'],
					'prestashop_language_id':data['presta_id'],
					'created_by':'Odoo',
					'name':data['name'],
					})
					returnid=prestashop.add('erp_language_merges', resource_data)
					return [True]
				else:
					raise Warning('Unkown Error')
		except:
			error_msg=reduce(lambda x, y: x+y,traceback.format_exception(*sys.exc_info()))
			return [False,error_msg]
			
	# _columns = {
	name =  fields.Many2one('res.lang', string='Language Name')
	erp_language_id = fields.Integer(string='Openerp`s Language Id')
	presta_language_id = fields.Integer(string='PrestaShop`s Language Id')
	presta_lang_select = fields.Selection(selection='_get_list',string='PrestaShop`s Language')
	erp_lang_select =  fields.Many2one('res.lang', string='OpenERP`s Language')
	code =  fields.Char(string='Locale Code', size=16,help='This field is used to set/get locales for user')
	# }
	
	@api.model
	def create(self,values):
		# if context is None:
		# 	context = {}
		if not 'prestashop' in self._context:
			if not values.get('erp_lang_select') or not values.get('presta_lang_select'):
				raise Warning('All fields are mandatory.')
			else:
				if int(values.get('presta_lang_select'))==-1:
					raise Warning('Sorry, Prestashop`s languages are not Available. Please check the configuration settings.')
				values['erp_language_id']=int(values.get('erp_lang_select'))
				values['presta_language_id']=int(values.get('presta_lang_select'))
				values['name']=int(values.get('erp_lang_select'))
				lang_data = self.env['res.lang'].browse(values['erp_language_id'])
				lang_data = lang_data.read(['code', 'name'])
				lang_data = lang_data[0]
				values['code']=lang_data['code']
				map_presta_end=self.addto_prestashop_merge({'erp_id':values.get('erp_lang_select'),'presta_id':values.get('presta_lang_select'),'name':lang_data['name']})
				if not map_presta_end[0]:
					raise Warning('Sorry, not able to create/check at prestashop`s end. \r\n\r\nPlease check at prestashop`s end. \r\n\r\nError:%s'%map_presta_end[1])
		else:
			lang_data = self.env['res.lang'].browse(values['erp_language_id'])
			lang_data = lang_data.read(['code', 'name'])
			if type(lang_data)==list:
				values['code']=lang_data[0]['code']
			else:
				values['code']=lang_data['code']
		return super(PrestashopLanguage, self).create(values)
		
	_sql_constraints = [
		('erp_language_id_unique', 'unique(erp_language_id)', 'Mapping for this OpenERP`s Language already exists!'),
		('presta_language_id_unique', 'unique(presta_language_id)', 'Mapping for this PrestaShop`s Language already exists!')
		]
PrestashopLanguage()


