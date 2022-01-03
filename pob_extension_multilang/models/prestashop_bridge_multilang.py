# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

# from openerp.osv import fields, osv
from odoo import api,models,fields
from odoo import tools
from odoo.exceptions import UserError,Warning
from odoo.tools.translate import _
from odoo.addons.pob.models import prestapi
from odoo.addons.pob.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError
from odoo.tools.translate import translate
from functools import reduce
import traceback,sys
import datetime
# from urllib.parse import unquote
from urllib.parse import unquote
import logging
_logger= logging.getLogger(__name__)
try:
	from odoo.loglevels import ustr as pob_decode
except:
	from odoo.tools.misc import ustr as pob_decode

# def _decode(name):
# 	# name = name.translate(None,'=+')
# 	name = unquote(name)
# 	#DB is corrupted with utf8 and latin1 chars.
# 	decoded_name = name
# 	if isinstance(name, str):
# 		try:
# 			decoded_name = name.encode('utf8')
# 		except:
# 			decoded_name = name
# 	else:
# 		try:
# 			decoded_name = str(name, 'utf8')
# 		except:
# 			try:
# 				decoded_name = str(name, 'latin1').encode('utf8')
# 			except:
# 				decoded_name = name
# 	return decoded_name
def _decode(text):
	if text.count("'") > 0:
		return text.split("'")[1]
	else:
		return text

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
	
############## Export To PrestaShop class #################
class PrestashoperpSyncNow(models.Model):			
	_inherit="prestashoperp.sync.now"
	
	@api.multi
	def _get_translated_value(self,presta_lang_id,default_value,translation_values):
		# if context is None:
		# 	context = {}
		if translation_values:
			for row in translation_values:
				if int(row['presta_language_id'])==int(presta_lang_id):
					return row['value']
		return default_value

	@api.multi
	def _get_translation_values(self,lang_map_ids,res_id,attr_name,type='model'):
		try:
			if lang_map_ids:
				map_lang_data=self.env['prestashop.language'].browse(lang_map_ids)
				map_lang_data=map_lang_data.read(['code','presta_language_id'])
				code_list=['test']				
				# getting all language codes in list
				for element in map_lang_data:
					code_list.append(_decode(element['code']))				
				query="SELECT value,lang,res_id FROM ir_translation where res_id=%s AND lang IN %s AND type='model' AND name=%s"%(repr(res_id),repr(tuple(code_list)),repr(attr_name))
				# raise Warning(query)
				try:
					self._cr.execute(query)
				except Exception as e:
					raise UserError('Erro%s'%str(map_lang_data+"\n"+query))
				db_response = self._cr.dictfetchall()				
				# converting unicode data
				for row in db_response:
					for element in row:
						if element=='lang':
							row[element]=_decode(row[element])
				
				for i in db_response:
					for j in map_lang_data:
						if i['lang'] == j['code']:
							i['presta_language_id']=j['presta_language_id']
				return db_response
			else:
				raise Warning('Can`t do Translation, no mapping(s) found!')
		except:
			error_message=reduce(lambda x, y: x+y,traceback.format_exception(*sys.exc_info()))
			raise Warning('Translation error.'+error_message)

	@api.multi
	def sync_categories(self,prestashop,cat_id,active='1'):
		# if context is None:
		# 	context={}
		context = self.env.context.copy() or {}
		lang_map_ids = self.env['prestashop.language'].search([])
		check=self.env['prestashop.category'].get_id('prestashop',cat_id)
		if not check:
			obj_catg=self.env['product.category'].browse(cat_id)			
			name=pob_decode(obj_catg.name)
			if obj_catg.parent_id.id:
				p_cat_id=self.sync_categories(prestashop,obj_catg.parent_id.id,1)[0]
			else:
				get_response=self.create_categories(prestashop,cat_id,name,'0','2',active,lang_map_ids.ids)
				p_cat_id=get_response[2]
				context['err_msg']+=get_response[1]
				return [p_cat_id,context['err_msg']]
			get_response=self.create_categories(prestashop,cat_id,name,'0',p_cat_id,active,lang_map_ids.ids)
			p_cat_id=get_response[2]
			context['err_msg']+=get_response[1]
			return [p_cat_id,context['err_msg']]
		else:
			return [check,context['err_msg']]

	@api.multi
	def export_update_cats(self,prestashop,erp_id,presta_id,map_id):
		# if context is None:
		# 	context = {}
		lang_map_ids = self.env['prestashop.language'].search([])
		obj_pro=self.env['product.category'].browse(erp_id)
		if obj_pro:
			if obj_pro.name:
				name=pob_decode(obj_pro.name)
			try:
				cat_data=prestashop.get('categories', presta_id)
			except Exception as e:
				return [0,' Error in Updating Category,can`t get category data %s'%str(e)]
			name_translation=False
			if lang_map_ids:
				name_translation=self._get_translation_values(lang_map_ids.ids,erp_id,'product.category,name')
			if type(cat_data['category']['name']['language'])==list:				
				for i in range(len(cat_data['category']['name']['language'])):
					presta_lang_id=cat_data['category']['name']['language'][i]['attrs']['id']
					tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
					cat_data['category']['name']['language'][i]['value']=tr_name
					cat_data['category']['link_rewrite']['language'][i]['value']=self._get_link_rewrite(zip,name)
			else:
				presta_lang_id=cat_data['category']['name']['language']['attrs']['id']				
				tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
				cat_data['category']['name']['language']['value']=tr_name
				cat_data['category']['link_rewrite']['language']['value']=self._get_link_rewrite(zip,name)
			a1=cat_data['category'].pop('level_depth',None)
			a2=cat_data['category'].pop('nb_products_recursive',None)
			try:
				returnid=prestashop.edit('categories',presta_id,cat_data)
			except Exception as e:
				return [0,' Error in updating Categoty(s) %s'%str(e)]
			if returnid:
				self._cr.execute("UPDATE prestashop_category SET need_sync='no' WHERE erp_category_id=%s"%erp_id)
				self._cr.commit()
	@api.multi
	def create_categories(self,prestashop,oe_cat_id,name,is_root_category,id_parent,active,lang_map_ids=False,link_rewrite='None',description='None',meta_description='None',meta_keywords='None',meta_title='None'):
		try:
			cat_data = prestashop.get('categories', options={'schema': 'blank'})
		except Exception as e:
			return [0,'\r\nCategory Id:%s ;Error in Creating blank schema for categories.Detail : %s'%(str(oe_cat_id),str(e)),False]
		if cat_data:
			name_translation=False
			if lang_map_ids:
				name_translation=self._get_translation_values(lang_map_ids,oe_cat_id,'product.category,name')
			if type(cat_data['category']['name']['language'])==list:
				for i in range(len(cat_data['category']['name']['language'])):
					presta_lang_id=cat_data['category']['name']['language'][i]['attrs']['id']
					tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
					cat_data['category']['name']['language'][i]['value']=tr_name
					cat_data['category']['link_rewrite']['language'][i]['value']=self._get_link_rewrite(zip,tr_name)
					cat_data['category']['description']['language'][i]['value']=description
					cat_data['category']['meta_description']['language'][i]['value']=meta_description
					cat_data['category']['meta_keywords']['language'][i]['value']=meta_keywords
					cat_data['category']['meta_title']['language'][i]['value']=meta_title
			else:
				presta_lang_id=cat_data['category']['name']['language']['attrs']['id']
				tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
				cat_data['category']['name']['language']['value']=tr_name
				cat_data['category']['link_rewrite']['language']['value']=self._get_link_rewrite(zip,name)
				cat_data['category']['description']['language']['value']=description
				cat_data['category']['meta_description']['language']['value']=meta_description
				cat_data['category']['meta_keywords']['language']['value']=meta_keywords
				cat_data['category']['meta_title']['language']['value']=meta_title
			cat_data['category']['is_root_category']=is_root_category
			cat_data['category']['id_parent']=id_parent
			cat_data['category']['active']=active
			try:
				returnid=prestashop.add('categories', cat_data)
			except Exception as e:
				return [0,'\r\nCategory Id:%s ;Error in creating Category(s).Detail : %s'%(str(oe_cat_id),str(e)),False]
			if returnid:
				cid=returnid
				self._cr.execute("INSERT INTO prestashop_category (category_name, erp_category_id, presta_category_id,need_sync) VALUES (%s, %s, %s,%s)", (oe_cat_id, oe_cat_id, cid,'no'))
				self._cr.commit()
				add_to_presta=self.addto_prestashop_merge(prestashop,'erp_category_merges',{'erp_id':oe_cat_id,'presta_id':cid})
				return [1,'',cid]

	@api.multi
	def action_multiple_synchronize_products(self):
		# if context is None:
		# 	context={}
		context = self.env.context.copy() or {}
		message = ''
		count = 0		
		need_to_export = []
		prod_obj = self.env['product.product']
		selected_ids = context.get('active_ids')		
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
			except Exception as  e:
				raise UserError(_('Error %s')%str(e))
			lang_map_ids=self.env['prestashop.language'].search([])
			context['lang_map_ids'] = lang_map_ids.ids
			if prestashop:
				product_bs = prestashop.get('products', options={'schema': 'blank'})
				combination_bs = prestashop.get('combinations', options={'schema': 'blank'})			
				for j in selected_ids:
					check = self.env['prestashop.product'].search([('erp_product_id','=',j)])
					if not check:
						need_to_export.append(j)
				if len(need_to_export)==0:
					message = 'Selected product(s) are already exported to Prestashop.'
				for erp_product_id in need_to_export:
					response = self.with_context(context).export_product(prestashop,product_bs,combination_bs,erp_product_id)
					if response[0]>0:
						count = count+1
			message = message+ '\r\n'+'%s products has been exported to Prestashop .\r\n'%(count)			
		
		partial_id = self.env['pob.message'].with_context(context).create({'text':message})
		return { 'name':_("Message"),
								 'view_mode': 'form',
								 'view_id': False,
								 'view_type': 'form',
								'res_model': 'pob.message',
								 'res_id': partial_id.id,
								 'type': 'ir.actions.act_window',
								 'nodestroy': True,
								 'target': 'new',
								 'domain': context,								 
							 }
		
	@api.multi
	def export_all_products(self):
		# if context is None:
		# 	context={}
		context = self.env.context.copy() or {}
		message = ''		
		count = 0
		map = []
		prod_obj = self.env['product.product']		
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
			except Exception as  e:
				raise UserError(_('Error %s')%str(e))
			lang_map_ids = self.env['prestashop.language'].search([])
			context['lang_map_ids'] = lang_map_ids.ids
			if prestashop:
				product_bs = prestashop.get('products', options={'schema': 'blank'})
				combination_bs = prestashop.get('combinations', options={'schema': 'blank'})
				already_mapped=self.env['prestashop.product'].search([])
				for m in already_mapped:
					map_obj=m				
					map.append(map_obj.erp_product_id)
				need_to_export=prod_obj.search([('id','not in',map),('type','not in',['service'])])				
				if len(need_to_export)==0:
					message = 'Nothing to Export. All product(s) are already exported to Prestashop.'
				for erp_product_id in need_to_export:
					response = self.with_context(context).export_product(prestashop,product_bs,combination_bs,erp_product_id.id)
					if int(response[0])>0:
						count = count+1
			message = message+ '\r\n'+'%s products has been exported to Prestashop .\r\n'%(count)		
		partial_id = self.with_context(context).env['pob.message'].create({'text':message})
		return {	'name':_("Message"),
					'view_mode': 'form',
					'view_id': False,
					'view_type': 'form',
					'res_model': 'pob.message',
					'res_id': partial_id.id,
					'type': 'ir.actions.act_window',
					'nodestroy': True,
					'target': 'new',
					'domain': context,								 
				}

	@api.multi
	def export_template(self,prestashop,product_bs,erp_template_id):
		# if context is None:
		# 	context={}		
		lang_map_ids = self._context['lang_map_ids']
		name_translation = False
		description_translation = False
		description_sale_translation = False
		obj_template = self.env['product.template']
		template_data = obj_template.browse(erp_template_id)
		erp_category_id = template_data.categ_id.id
		presta_default_categ_id=self.with_context({'err_msg':''}).sync_categories(prestashop,erp_category_id,1)[0]
		product_bs['product'].update({
								 'price': str(template_data.list_price),
								 'active':'1',
								 'redirect_type':'404',
								 'minimal_quantity':'1',
								 'available_for_order':'1',
								 'show_price':'1',
								 'out_of_stock':'2',
								 'condition':'new',									
								 'id_category_default':str(presta_default_categ_id)									 
								})
		if lang_map_ids:
			name_translation=self._get_translation_values(lang_map_ids, erp_template_id, 'product.template,name')
			description_translation=self._get_translation_values(lang_map_ids, erp_template_id, 'product.template,description')
			description_sale_translation=self._get_translation_values(lang_map_ids, erp_template_id, 'product.template,description_sale')
		# raise osv.except_osv(_('Context'),_('name=%s...desc=%s')%(name_translation,description_translation))
		if type(product_bs['product']['name']['language'])==list:
			for i in range(len(product_bs['product']['name']['language'])):
				presta_lang_id = product_bs['product']['name']['language'][i]['attrs']['id']
				tr_name=self._get_translated_value(presta_lang_id,template_data.name,name_translation)
				product_bs['product']['name']['language'][i]['value'] = tr_name
				product_bs['product']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite(zip,tr_name)
				product_bs['product']['description']['language'][i]['value'] = self._get_translated_value(presta_lang_id,template_data.description,description_translation)
				product_bs['product']['description_short']['language'][i]['value'] = self._get_translated_value(presta_lang_id,template_data.description_sale,description_sale_translation)
		else:
			presta_lang_id=product_bs['product']['name']['language']['attrs']['id']
			tr_name = self._get_translated_value(presta_lang_id, template_data.name, name_translation)
			tr_desc = self._get_translated_value(presta_lang_id, template_data.description, description_translation)
			tr_sale_desc = self._get_translated_value(presta_lang_id, template_data.description_sale, description_sale_translation)
			product_bs['product']['name']['language']['value']=tr_name
			product_bs['product']['link_rewrite']['language']['value']=self._get_link_rewrite(zip,name)
			product_bs['product']['description']['language']['value']=tr_desc
			product_bs['product']['description_short']['language']['value']=tr_sale_desc

		product_bs['product']['associations']['categories']['category']['id']=str(presta_default_categ_id)
		pop_attr=product_bs['product']['associations'].pop('combinations',None)
		a1=product_bs['product']['associations'].pop('images',None)
		try:
			returnid=prestashop.add('products', product_bs)
		except Exception as e:
			return [0,' Error in creating Product Template(ID: %s).%s'%(str(presta_default_categ_id),str(e))]
		if returnid:
			self._cr.execute("INSERT INTO prestashop_product_template (template_name, erp_template_id, presta_product_id,need_sync) VALUES (%s, %s, %s,%s)", (erp_template_id, erp_template_id, returnid,'no'))
			self._cr.commit()
			add_to_presta=self.addto_prestashop_merge(prestashop,'erp_product_template_merges',{'erp_id':erp_template_id,'presta_id':returnid})
			return [returnid,'']
		return [0,'Unknown Error']

	@api.multi
	def update_product_prestashop(self):
		# if context is None:
		# 	context={}
		context = self.env.context.copy() or {}
		message = ''
		error_message = ''
		update = 0		
		map = []
		prod_obj = self.env['product.product']
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
			except Exception as  e:
				raise UserError(_('Error %s')%str(e))
			lang_map_ids = self.env['prestashop.language'].search([])
			context.update({'lang_map_ids' : lang_map_ids.ids})
			if prestashop:			
				need_update_id=self.env['prestashop.product'].search([('need_sync','=','yes')])
				if len(need_update_id)==0:
					message = 'Nothing to Update. All product(s) are already updated to Prestashop.'
				if need_update_id:
					pp_obj=self.env['prestashop.product']
					for m in need_update_id:
						attribute_id=m.presta_product_attr_id
						presta_id=m.presta_product_id
						# raise osv.except_osv(_('Error!'),_('presta_id=%s')%(presta_id))	
						erp_id=m.erp_product_id
						if int(attribute_id)>=0 and int(presta_id) not in [0,-1]:
							response=self.with_context(context).export_update_products(prestashop,erp_id,presta_id,attribute_id)
							if response[0]==0:								
								error_message+=response[1]
							else:
								update+=1
						
					if len(error_message)==0:
						message = message+ '\r\n'+'%s Products Successfully Updated to Prestashop .\r\n'%(update)
					else:
						message = message+ '\r\n'+'Error in Updating product(s): %s.\r\n'%(error_message)
			partial_id = self.with_context(context).env['pob.message'].create({'text':message})
			return { 'name':_("Message"),
								 'view_mode': 'form',
								 'view_id': False,
								 'view_type': 'form',
								'res_model': 'pob.message',
								 'res_id': partial_id.id,
								 'type': 'ir.actions.act_window',
								 'nodestroy': True,
								 'target': 'new',
								 'domain': context,								 
							 }

	@api.multi
	def update_products(self,prestashop,erp_id,presta_id,attribute_id,name,price,quantity,id_category_default='2',condition='new',description='None',description_short='None',image_data=False,default_code='',ean13=''):
		# if context is None:
		# 	context = {}
		# raise osv.except_osv(_('Error!'),_('update context=%s')%(context))
		# message='Error in Updating Product with ERP-ID '+str(erp_id)
		context = self.env.context.copy() or {}
		message=''
		if int(presta_id) in [0,-1,-2,-3]:
			self._cr.execute("UPDATE prestashop_product SET need_sync='no' WHERE erp_product_id=%s"%erp_id)
			self._cr.commit()
		else:
			try:
				product_data=prestashop.get('products', presta_id)
			except Exception as e:
				return [0,' Error in Updating Product,can`t get product data %s'%str(e)]
			if product_data:
				name_translation = False
				description_translation = False
				description_sale_translation = False
				if int(attribute_id)==0:
					product_data['product'].update({
										 'price': price,										 
										 'reference':default_code,
										 'ean13':ean13											
										})

					if 'weight' in context:
						product_data['product']['weight']=str(context['weight'])
					if type(product_data['product']['name']['language'])==list:
						for i in range(len(product_data['product']['name']['language'])):
							presta_lang_id=product_data['product']['name']['language'][i]['attrs']['id']
							tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
							product_data['product']['name']['language'][i]['value']=tr_name
							product_data['product']['link_rewrite']['language'][i]['value']=self._get_link_rewrite(zip,tr_name)
							product_data['product']['description']['language'][i]['value']=self._get_translated_value(presta_lang_id,description,description_translation)
							product_data['product']['description_short']['language'][i]['value']=self._get_translated_value(presta_lang_id,description_short,description_sale_translation)
					else:
						presta_lang_id=product_data['product']['name']['language']['attrs']['id']
						tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
						tr_desc=self._get_translated_value(presta_lang_id,name,description_translation)
						tr_sale_desc=self._get_translated_value(presta_lang_id,name,description_sale_translation)
						product_data['product']['name']['language']['value']=tr_name
						product_data['product']['link_rewrite']['language']['value']=self._get_link_rewrite(zip,name)
						product_data['product']['description']['language']['value']=tr_desc
						product_data['product']['description_short']['language']['value']=tr_sale_desc
					# product_data['product']['associations']['categories']['category']['id']=id_category_default
					a1=product_data['product'].pop('position_in_category',None)
					a2=product_data['product'].pop('manufacturer_name',None)
					a3=product_data['product'].pop('quantity',None)
					a4=product_data['product'].pop('type',None)
					try:
						returnid=prestashop.edit('products',presta_id,product_data)						
					except Exception as e:
						return [0,' Error in updating Product(s) %s'%str(e)]
					except Exception as e:
						return [0,' Error in updating Product(s) %s'%str(e)]
					if not 'image' in product_data['product']['associations']['images']:
						if image_data:
							get=self.create_images(prestashop,image_data,presta_id)
					up=True
				else:
					resp=self.with_context(context).update_products_with_attributes(prestashop,erp_id,presta_id,attribute_id,price,default_code,ean13)
					returnid=resp[0]
					up=False
					message =message+resp[1]
				if returnid:
					if up:
						if not 'template' in context:
							self._cr.execute("UPDATE prestashop_product SET need_sync='no' WHERE erp_product_id=%s"%(erp_id))
							self._cr.commit()
						# else:
						# 	cr.execute("UPDATE prestashop_product_template SET base_price=%s WHERE erp_template_id=%s"%(price,erp_id))
						# 	cr.commit()
					if type(product_data['product']['associations']['stock_availables']['stock_available'])==list:
						for data in product_data['product']['associations']['stock_availables']['stock_available']:
							if int(data['id_product_attribute'])==int(attribute_id):
								stock_id=data['id']
					else:
						stock_id=product_data['product']['associations']['stock_availables']['stock_available']['id']
					if float(quantity) > 0.0:
						return self.with_context(context).update_quantity(prestashop,presta_id,quantity,stock_id,attribute_id)
					else:
						return [1,'']
				else:
					return [0,message]

	@api.multi
	def create_dimension_type(self,prestashop,add_data,erp_dim_type_id,name):
		# if context is None:
		# 	context = {}
		lang_map_ids = self.env['prestashop.language'].search([])			
		if add_data:
			add_data['product_option'].update({
										'group_type': 'select',
										'position':'0'
										})
			name_translation = False
			if lang_map_ids:
				name_translation=self._get_translation_values(lang_map_ids.ids,erp_dim_type_id,'product.attribute,name')
			if type(add_data['product_option']['name']['language'])==list:				
				for i in range(len(add_data['product_option']['name']['language'])):
					presta_lang_id = add_data['product_option']['name']['language'][i]['attrs']['id']
					tr_name = self._get_translated_value(presta_lang_id,name,name_translation)
					add_data['product_option']['name']['language'][i]['value'] = tr_name
					add_data['product_option']['public_name']['language'][i]['value'] = tr_name
			else:
				presta_lang_id=add_data['product_option']['name']['language']['attrs']['id']
				tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
				add_data['product_option']['name']['language']['value']=tr_name
				add_data['product_option']['public_name']['language']['value']=tr_name
			try:
				returnid=prestashop.add('product_options', add_data)
			except Exception as e:
				return [0,' Error in creating Dimension Type(ID: %s).%s'%(str(erp_dim_type_id),str(e))]
			if returnid:
				pid=returnid
				self._cr.execute("INSERT INTO prestashop_product_attribute (name,erp_id,presta_id,need_sync) VALUES (%s, %s, %s,%s)", (erp_dim_type_id, erp_dim_type_id, pid,'no'))
				self._cr.commit()
				add_to_presta=self.addto_prestashop_merge(prestashop,'erp_attributes_merges',{'erp_id':erp_dim_type_id,'presta_id':pid})
				return [pid,'']

	@api.multi
	def create_dimension_option(self,prestashop,erp_attr_id,add_value,presta_attr_id,erp_dim_opt_id,name):
		# if context is None:
		# 	context = {}
		lang_map_ids = self.env['prestashop.language'].search([])
		if add_value:
			add_value['product_option_value'].update({
										'id_attribute_group': presta_attr_id,
										'position':'0'
													})
			name_translation=False
			if lang_map_ids:
				name_translation=self._get_translation_values(lang_map_ids.ids,erp_dim_opt_id,'product.attribute.value,name')
			if type(add_value['product_option_value']['name']['language'])==list:
				for i in range(len(add_value['product_option_value']['name']['language'])):
					presta_lang_id = add_value['product_option_value']['name']['language'][i]['attrs']['id']
					tr_name = self._get_translated_value(presta_lang_id,name,name_translation)
					add_value['product_option_value']['name']['language'][i]['value']=tr_name
			else:
				presta_lang_id=add_value['product_option_value']['name']['language']['attrs']['id']
				tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
				add_value['product_option_value']['name']['language']['value']=tr_name
			try:
				returnid=prestashop.add('product_option_values', add_value)
			except Exception as e:
				return [0,' Error in creating Dimension Option(ID: %s).%s'%(str(erp_dim_opt_id),str(e))]
			if returnid:
				pid=returnid
				self._cr.execute("INSERT INTO prestashop_product_attribute_value (name,erp_id,presta_id,erp_attr_id,presta_attr_id,need_sync) VALUES (%s, %s, %s, %s, %s, %s)", (erp_dim_opt_id, erp_dim_opt_id, pid, erp_attr_id, presta_attr_id, 'no'))
				self._cr.commit()
				add_to_presta=self.addto_prestashop_merge(prestashop,'erp_attribute_values_merges',{'erp_value_id':erp_dim_opt_id,'presta_id':pid,'presta_attr_id':presta_attr_id,'erp_attr_id':erp_attr_id})
				return [pid,'']



	@api.multi
	def action_multiple_synchronize_templates(self):
		# if context is None:
		# 	context = {}		
		context = self.env.context.copy() or {}
		message= ''
		count= 0
		temp = context.get('active_ids')		
		need_to_export = []	
		exported_ids = []	
		erp_product_ids = []
		config_id = self.env['prestashop.configure'].search([('active','=',True)])
		if not config_id:
			raise UserError(_("Connection needs one Active Configuration setting."))
		if len(config_id)>1:
			raise UserError(_("Sorry, only one Active Configuration setting is allowed."))
		else:
			obj=config_id[0]
			key = obj.api_key
			url = obj.api_url						
			try:
				prestashop = PrestaShopWebServiceDict(url,key)
			except Exception as  e:
				raise osv.except_osv(_('Error %s')%str(e))
			lang_map_ids = self.env['prestashop.language'].search([])
			context['lang_map_ids'] = lang_map_ids.ids
			for i in temp:	
				search = self.env['prestashop.product.template'].search([('erp_template_id','=',i)])
				if search:
					exported_ids.append(i)
				else:
					need_to_export.append(i)		
			if exported_ids and prestashop:		
				for j in exported_ids:								
					pp_obj = self.env['prestashop.product.template']
					need_update_id = pp_obj.search([('erp_template_id','=',j)])
					presta_id = pp_obj.browse(need_update_id[0].id).presta_product_id
					erp_id = j					
					if prestashop and need_update_id:				
						temp_obj = self.env['product.template'].browse(erp_id)					
						if temp_obj:							
							if not temp_obj.name:
								name='None'
							else:							
								name=temp_obj.name					
							if temp_obj.description:
								description = temp_obj.description
							else:
								description = ' '
							if temp_obj.description_sale:
								description_sale = temp_obj.description_sale
							else:
								description_sale=' '
							if temp_obj.list_price:
								price = temp_obj.list_price
							else:
								price = 0.0
							if temp_obj.weight:
								weight = temp_obj.weight
							else:
								weight = 0.000000
							if temp_obj.standard_price:
								cost = temp_obj.standard_price
							else: 
								cost = 0.0
							if temp_obj.categ_id:
								def_categ = temp_obj.categ_id.id
							else:
								raise UserError(_('Template Must have a Default Category')%())		

							update = self.with_context({'price':price,'weight':weight,'cost':cost, 'def_categ':def_categ,'lang_map_ids':lang_map_ids.ids}).update_template(prestashop, erp_id, presta_id, name, description, description_sale)
			if need_to_export and prestashop:
				for k in self.env['product.template'].browse(need_to_export):
					for l in k.product_variant_ids:
						erp_product_ids.append(l.id)
				prod_ids = self.env['product.product'].search([('id','in',erp_product_ids),('type','not in',['service'])])
				product_bs = prestashop.get('products', options={'schema': 'blank'})
				combination_bs = prestashop.get('combinations', options={'schema': 'blank'})				
				for erp_product_id in prod_ids:
					response = self.with_context(context).export_product(prestashop,product_bs,combination_bs,erp_product_id.id)			
			message = 'Product Template(s) Updated: %s\r\nNumber of Product Template(s) Exported: %s'%(len(exported_ids),len(need_to_export))+' \r\n'+message			
		partial_id = self.env['pob.message'].with_context(context).create({'text':message})
		return { 'name':_("Message"),
						 'view_mode': 'form',
						 'view_id': False,
						 'view_type': 'form',
						 'res_model': 'pob.message',
						 'res_id': partial_id.id,
						 'type': 'ir.actions.act_window',
						 'nodestroy': True,
						 'target': 'new',
						 'domain': context,								 
					 }
						
					
	@api.multi
	def update_template(self,prestashop, erp_id, presta_id, name, description, description_sale):
		# if context is None:
		# 	context = {}
		context = self.env.context.copy() or {}
		message=''
		lang_map_ids = context['lang_map_ids']		
		template_data = self.with_context(context).update_template_category(prestashop, erp_id, presta_id)	
		if template_data:			
			if 'price' in context:
				template_data['product']['price'] = str(context['price'])
			if 'cost' in context:
				template_data['product']['wholesale_price'] = str(context['cost'])			
			if 'weight' in context:
				template_data['product']['weight'] = str(context['weight'])
			if lang_map_ids:
				name_translation=self._get_translation_values(lang_map_ids, erp_id, 'product.template,name')
				description_translation=self._get_translation_values(lang_map_ids, erp_id, 'product.template,description')
				description_sale_translation=self._get_translation_values(lang_map_ids, erp_id, 'product.template,description_sale')
			if type(template_data['product']['name']['language'])==list:
				for i in range(len(template_data['product']['name']['language'])):
					presta_lang_id = template_data['product']['name']['language'][i]['attrs']['id']
					tr_name=self._get_translated_value(presta_lang_id,name,name_translation)
					template_data['product']['name']['language'][i]['value'] = tr_name
					template_data['product']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite(zip,tr_name)
					template_data['product']['description']['language'][i]['value'] = self._get_translated_value(presta_lang_id,description,description_translation)
					template_data['product']['description_short']['language'][i]['value'] = self._get_translated_value(presta_lang_id,description_sale,description_sale_translation)
			else:
				presta_lang_id=template_data['product']['name']['language']['attrs']['id']
				tr_name = self._get_translated_value(presta_lang_id, name, name_translation)
				tr_desc = self._get_translated_value(presta_lang_id, description, description_translation)
				tr_sale_desc = self._get_translated_value(presta_lang_id, description_sale, description_sale_translation)
				template_data['product']['name']['language']['value']=tr_name
				template_data['product']['link_rewrite']['language']['value']=self._get_link_rewrite(zip,name)
				template_data['product']['description']['language']['value']=tr_desc
				template_data['product']['description_short']['language']['value']=tr_sale_desc

			a1 = template_data['product'].pop('position_in_category',None)
			a2 = template_data['product'].pop('manufacturer_name',None)
			a3 = template_data['product'].pop('quantity',None)
			a4 = template_data['product'].pop('type',None)				
			# try:
			returnid=prestashop.edit('products',presta_id,template_data)
			# except Exception as e:
			# 	# raise osv.except_osv(_('Error!'),_('template_bfgbdata=%s')%(e))
			# 	return [0,' Error in updating Template(s) %s'%str(e)]			
			if returnid:									
				self._cr.execute("UPDATE prestashop_product_template SET need_sync='no' WHERE template_name=%s"%(erp_id))
				self._cr.commit()
				return [1,'Template Successfully Updated']
								
			else:
				return [0,str(e)]

	@api.multi
	def addto_prestashop_merge(self,prestashop,resource,data):
		try:
			resource_data = prestashop.get(resource, options={'schema': 'blank'})
		except Exception as e:
			return [0,' Error in Creating blank schema for resource.']
		if resource_data:
			if resource=='erp_attributes_merges':
				resource_data['erp_attributes_merge'].update({
					'erp_attribute_id':data['erp_id'],
					'prestashop_attribute_id':data['presta_id'],
					'translate_state':'translated',
					'color':'LimeGreen',
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Product.']
			if resource=='erp_attribute_values_merges':
				resource_data['erp_attribute_values_merge'].update({
					'erp_attribute_id':data['erp_attr_id'],
					'erp_attribute_value_id':data['erp_value_id'],
					'prestashop_attribute_value_id':data['presta_id'],
					'prestashop_attribute_id':data['presta_attr_id'],
					'translate_state':'translated',
					'color':'LimeGreen',
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Product.']
			if resource=='erp_product_merges':
				resource_data['erp_product_merge'].update({
					'erp_product_id':data['erp_id'],
					'erp_template_id':data['erp_temp_id'],
					'prestashop_product_id':data['presta_id'],
					'prestashop_product_attribute_id':data.get('prestashop_product_attribute_id','0'),
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Product.']
			if resource=='erp_product_template_merges':
				resource_data['erp_product_template_merge'].update({
					'erp_template_id':data['erp_id'],
					'presta_product_id':data['presta_id'],
					'translate_state':'translated',
					'color':'LimeGreen',
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Template.']
			if resource=='erp_category_merges':
				resource_data['erp_category_merge'].update({
					'erp_category_id':data['erp_id'],
					'prestashop_category_id':data['presta_id'],
					'translate_state':'translated',
					'color':'LimeGreen',
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Category.']
			if resource=='erp_customer_merges':
				resource_data['erp_customer_merge'].update({
					'erp_customer_id':data['erp_id'],
					'prestashop_customer_id':data['presta_id'],
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Customer.']
			if resource=='erp_address_merges':
				resource_data['erp_address_merge'].update({
					'erp_address_id':data['erp_id'],
					'prestashop_address_id':data['presta_id'],
					'id_customer':data['presta_cust_id'],
					'created_by':'OpenERP',
					})
				try:
					returnid=prestashop.add(resource, resource_data)
					return [1,'']
				except Exception as e:
					return [0,' Error in Creating Entry in Prestashop for Customer.']
		return [0,' Unknown Error in Creating Entry in Prestashop.']

	
PrestashoperpSyncNow()

