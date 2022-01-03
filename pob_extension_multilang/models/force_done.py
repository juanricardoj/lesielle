# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,models,fields
from odoo import tools
from odoo.exceptions import UserError,Warning
from odoo.tools.translate import _
from odoo.addons.pob.models import prestapi
from odoo.addons.pob.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError
from odoo.tools.translate import translate
import traceback,sys
import datetime
import urllib3
import logging
_logger = logging.getLogger(__name__)

try:
	from odoo.loglevels import ustr as pob_decode
except:
	from odoo.tools.misc import ustr as pob_decode

def _decode(name):
	# name = name.translate(None,'=+')
	name = urllib3.unquote(name)
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

############## Inherited PrestaShop classes #################
class ForceDone(models.Model):			
	_inherit="force.done"
	
	# @api.multi
	# def _create_translation(self,lang_code,trans_field_name,res_id,value):
	# 	# if context is None: 
	# 	# 	context = {}
	# 	# cr.execute("UPDATE ir_translation SET  value=%s WHERE lang=%s and name=%s and res_id=%s and type='model'", (value,lang_code,trans_field_name,res_id))
	# 	# cr.commit()
	# 	#--------------------------------------------------start----------------------------------------------------------
	# 	_logger.info('-------------wk----------%r',type(lang_code))
	# 	if not lang_code:
	# 		return True
	# 	self._cr.execute("SELECT id FROM ir_translation WHERE lang = %d and name='%s' and res_id=%s and type='model'"%(lang_code,trans_field_name,res_id))
	# 	result = self._cr.fetchone()
	# 	_logger.info('-----------------------------------wk----------------%r',result)
	# 	if result:
	# 		trans_id=result[0]
	# 		#----------------------------------------------------------stop--------------------------------------------------
	# 		# cr.execute("SELECT id FROM ir_translation WHERE id=%s"%trans_id)
	# 		# r=cr.fetchone()
	# 		# raise Warning('Can`t %s!'%str(r[0]))
	# 		#----------------------------------------------------------start-------------------------------------------------
	# 		self._cr.execute("UPDATE ir_translation SET value='%s',state='%s' WHERE id=%d"%(value,'translated',trans_id))
	# 	else:
	# 		self._cr.execute("INSERT INTO ir_translation (lang,name,res_id,value,type,state) VALUES(%s,'%s',%s,'%s','%s','%s')"%(lang_code,trans_field_name,res_id,value,'model','translated'))
	# 	self._cr.commit()
	# 	return True
	# 	#---------------------------------------------------------------stop-------------------------------------------------
	
	@api.multi
	def _create_translation(self,lang_code,trans_field_name,res_id,value):
		if not lang_code:
			return True
		records=self.env['ir.translation'].search([('lang','=',lang_code),('name','=',trans_field_name),('res_id','=',res_id),('type','=','model')])	
		if records:
			records[0].write({'value':value,'state':'translated'})
		else:
			rec=self.env['ir.translation'].create({'lang':lang_code,'name':trans_field_name,'res_id':res_id,'value':value,'type':'model','state':'translated'})
		return True		



	@api.model
	def import_translation(self,model,data):
		error_message=''
		if not isinstance(data,list):
			raise Warning("Prestashop`s data must be in 'list' format but found in '%s'!"%type(data))
		# if not isinstance(data[0],dict):
			# raise Warning("Prestashop`s data must contain 'dictionary' format but found in '%s'!"%type(data[0]))
		for row in data:
			for element in row:
				lang_map_id=self.env['prestashop.language'].search([('presta_language_id','=',row['lang_id'])])
				if lang_map_id:
					lang_code=lang_map_id[0].code
					if element=='name' and model=='product':
						self._create_translation(lang_code,'product.template,name',row['erp_id'],_unescape(row[element]))
					if element=='description' and model=='product':
						self._create_translation(lang_code,'product.template,description',row['erp_id'],_unescape(row[element]))
					if element=='description_sale' and model=='product':
						self._create_translation(lang_code,'product.template,description_sale',row['erp_id'],_unescape(row[element]))
					if element=='name' and model=='category':
						self._create_translation(lang_code,'product.category,name',row['erp_id'],_unescape(row[element]))
					if element=='name' and model=='attribute':
						self._create_translation(lang_code,'product.attribute,name',row['erp_id'],_unescape(row[element]))
					if element=='name' and model=='attribute_value':
						self._create_translation(lang_code,'product.attribute.value,name',row['erp_id'],_unescape(row[element]))
		return True
		
			
ForceDone()
