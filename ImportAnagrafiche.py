# -*- encoding: utf-8 -*-

import decimal_precision as dp
import time
import base64
from tempfile import TemporaryFile
import math
from osv import fields, osv
import tools
import ir
import pooler
import tools
import threading
from tools.translate import _
import csv
import sys
import os
import re

def mult_add(i, j):
    """Sum each digits of the multiplication of i and j."""
    return reduce(lambda x, y: x + int(y), str(i*j), 0)

def check_vat_it(vat):
        '''
        Check Italy VAT number.
        '''
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except:
            return False
        if int(vat[0:7]) <= 0:
            return False
        if int(vat[7:10]) <= 0:
            return False
        if int(vat[7:10]) > 100 and int(vat[7:10]) < 120:
            return False
        if int(vat[7:10]) > 121:
            return False

        sum = int(vat[0]) + mult_add(2, int(vat[1])) + int(vat[2]) + \
                mult_add(2, int(vat[3])) + int(vat[4]) + \
                mult_add(2, int(vat[5])) + int(vat[6]) + \
                mult_add(2, int(vat[7])) + int(vat[8]) + \
                mult_add(2, int(vat[9]))
        check = 10 - (sum % 10)
        if check == 10:
            check = 0
        if check != int(vat[10]):
            return False
        return True

class res_partner(osv.osv):

    _inherit='res.partner'
    _columns = {         
                'meseprimoescluso': fields.integer('1 Mese Escluso'),
                'mesesecondoescluso': fields.integer('2 Mese Escluso'),
                'giornoescluso': fields.integer('Giorno Escluso'),
                'credagenti':fields.char('Crediti Agenti',size=1),
                'bloccato':fields.boolean('Partner Bloccato'),
                'moratoria':fields.boolean('Partner in Contenzioso'),
                
                }


res_partner()

class import_anagrafiche(osv.osv_memory):
    _name = 'import.anagrafiche'
    _description = 'Permette di importare i dati  csv delle anagrafiche di ad-hoc'
    _columns = {
         'clienti_base':fields.boolean('Clienti Base'),
         'fornitori_base':fields.boolean('Fornitori Base'),
         'clienti_indirizzi_base':fields.boolean('Indirizzi Base Clienti'),
         'fornitori_indirizzi_base':fields.boolean('Indirizzi Base Clienti'),
         'des_dive_cli':fields.boolean('Destinazioni Diverse Clienti/Fornitori'),
         'banche':fields.boolean('Banche'),
         'pagamenti':fields.boolean('Pagamenti'),
         'piacont':fields.boolean('Piano dei Conti'),
         'data': fields.binary('File csv di Import', required=True),
 
         
    }
    
    
    def _import_desdive(self,cr,uid,lines,context):
     inseriti = 0
     aggiornati = 0
     for line in lines:
            # Mappatura attributi/CSV
        print line
        line = line.replace('"', '')
        line = line.replace('\n', '')
        line = line.replace(',', '.')
        line = line.split(";")        
        tipo = line[0].strip()
        codice = "%07d" % (int(line[1].strip())) 
        if tipo == 'F':
            codcice = 'F'+codice
        #print codice ,  "%07d" % (int(line[0].strip())), line[0].strip(),line[0]
        descrizione = line[3].strip()
        indirizzo = line[4].strip()
        cap = line[5].strip()
        localita = line[6].strip()
        prov = line[7].strip()
        #import pdb;pdb.set_trace()
        note = line[8].strip()
        partner_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',codice)])
        if partner_id:
            partner_id = partner_id[0]
            city_id = self.pool.get('res.city').search(cr,uid, [('name', '=', localita.title())])
            inseriti += 1
            if city_id:
                citta = self.pool.get('res.city').browse(cr,uid,city_id)[0]
                Indirizzo =  {
                  'partner_id':partner_id,
                  'type':'delivery',
                  'street': indirizzo,
                  'city':citta['name'],
                  'zip':citta['zip'],
                  'province':citta['province_id'].id,
                  'region':citta['region'].id,       
                  'phone':note,
                  'name':descrizione,
                  
                  }
            else:
                Indirizzo =  {
                  'partner_id':partner_id,
                  'type':'delivery',
                  'street': indirizzo,
                  'city':localita,
                  'zip':cap,
                  'phone':note,
                  'name':descrizione,
                  
                  }
            id_address = self.pool.get('res.partner.address').create(cr,uid,Indirizzo)
                

            
     return [inseriti, aggiornati]
    

    def _import_banche(self,cr,uid,lines,context):
     inseriti = 0
     aggiornati = 0
     for line in lines:
            # Mappatura attributi/CSV
        #print line
        line = line.replace('"', '')
        line = line.replace('\n', '')
        line = line.replace(',', '.')
        line = line.split(";")        
        codice = "%07d" % (int(line[0].strip())) 
        #print codice ,  "%07d" % (int(line[0].strip())), line[0].strip(),line[0]
        descrizione = line[1].strip()
        indirizzo = line[2].strip()
        cap = line[3].strip()
        citta = line[4].strip()
        prov = line[5].strip()
        #import pdb;pdb.set_trace()
        if line[6].strip().isdigit():
                abi = "%05d" % (int(line[6].strip()))
        else:
                abi = line[6].strip()
        if line[7].strip().isdigit():
                cab = "%05d" % (int(line[7].strip()))
        else:
                    cab=line[7].strip()
        sottoconto = line[8].strip()
        flgriba = line[9].strip()
        numconto = line[10].strip()
     
        # import pdb;pdb.set_trace()
        idsbanc = self.pool.get('res.bank').search(cr,uid,[('code','=',codice)])
       
        if idsbanc:
            bb = self.pool.get('res.bank').browse(cr,uid,idsbanc)
            # record trovato
            banca = {
                          'code':codice,
                          'name':descrizione,
                          'zip':cap,
                          'street':indirizzo,
                          'city':citta,
                          'codice_abi':abi,
                          'codice_cab':cab,
                          
                         
                          }
            ok = self.pool.get('res.bank').write(cr,uid,idsbanc,banca)
            aggiornati += 1
        else:
            #import pdb;pdb.set_trace()
            banca = {
                          'code':codice,
                          'name':descrizione,
                          'zip':cap,
                          'street':indirizzo,
                          'city':citta,
                          'codice_abi':abi,
                          'codice_cab':cab,
                          
                         
                          }
            ok = self.pool.get('res.bank').create(cr,uid,banca)
            inseriti += 1
        
     #import pdb;pdb.set_trace()   
     return [inseriti, aggiornati]
    

    def _import_ana_base(self,cr, uid, lines,tipo, context):
     inseriti = 0
     aggiornati = 0
     for line in lines:
            # Mappatura attributi/CSV
        #print line
        line = line.replace('"', '')
        line = line.replace('\n', '')
        line = line.replace(',', '.')
        line = line.split(";")        
     #import pdb;pdb.set_trace()
        #print line[0].strip()
        codice = "%07d" % (int(line[0].strip())) 
        
        if tipo=="F":
            codice=tipo+codice
        ragsoc = line[1].strip()
        ragsoc2 = line[2].strip()
        indirizzo = line[3].strip()
        cap = line[4].strip()
        localita = line[5].strip()
        prov = line[6].strip()
        nazione = line[7].strip()
        tel = line[8].strip()
        if tel.isdigit():
            tel="0"+tel
        fax = line[9].strip()
        if fax.isdigit():
            fax="0"+fax
        cell = line[10].strip()
        if cell.isdigit():
            cell=str(cell)
        codfiscale = line[16].strip()
        piva = str(line[17].strip())    
        pagamento = "%04d" % (int(line[21].strip()))   
        vettore = str(line[22].strip())
        spedizione = str(line[23].strip())
        porto = str(line[24].strip())
        zona = "%04d" % (int(line[25].strip()))
        agente = str(line[26].strip())
        agente2 = str(line[27].strip())
        cod_esenzione_iva= str(line[28].strip())
        codeseconai = line[56].strip()
        bloccato=line[47].strip()
        moratoria=line[48].strip()
        creditiagenti = line[74].strip()
        valuta= str(line[29].strip())
        if line[30].strip():
          bancaclifor = "%07d" % (int(line[30].strip()))
        if line[31].strip():
          bancaazienda = "%07d" % (int(line[31].strip()))
        meseescluso1 = str(line[32].strip())
        meseescluso2 = str(line[33].strip())
        gornoescluso = str(line[34].strip())
        listino = line[37].strip()
        codicenazione = line[44].strip()
        numero_cc =  line[45].strip()
        email = line[75].strip()
        # Controllo PIVA
        if nazione == 'ITA' and len(piva)==9:
            piva = '00'+piva           
        if nazione == 'ITA' and len(piva)==10:
            piva = '0'+piva            
        if not check_vat_it(piva) and nazione == 'ITA':
            piva = False
        else:
            piva = 'IT'+piva            
        if nazione != 'ITA':
            piva = False        
        try:
            codfiscale = int(codfiscale)
        except:
            pass        
        if isinstance(codfiscale,int) or isinstance(codfiscale,long):
           if nazione == 'ITA' and len(str(codfiscale))==9:
             codfiscale = '00'+str(codfiscale)
           elif nazione == 'ITA' and len(str(codfiscale))==10:
             codfiscale = '0'+str(codfiscale)
        if zona:
            # CERCA LA ZONA CLIENTE NELLA CATEGORIA CLIENTE QUESTO IMPLICA CHE DEVONO ESSERE STATE CARICATE PRIMA
            args = [('name', 'ilike', zona+"%")]
            ids_zona = self.pool.get('res.partner.category').search(cr,uid, args)  
            if not ids_zona:
              ids_zona=[0]
        else:
            ids_zona=[0]
        if type(codfiscale)<>'str':
          codfiscale = str(codfiscale)
        if cod_esenzione_iva:
            if cod_esenzione_iva==8:
                cod_esenzione_iva= False
            else:
                # cerca l'id del codice di esenzione
                id_iva = self.pool.get('account.tax').search(cr,uid,[('description','=',str(cod_esenzione_iva))])
                if id_iva:
                    id_iva = id_iva[0]
                else:
                    id_iva = False
        else:
            cod_esenzione_iva = False
        if agente:
            id_agente = self.pool.get('sale.agent').search(cr,uid,[('name','ilike',agente+"--%")])  
            if id_agente:
                id_agente=id_agente[0]
            else:
                id_agente=False
        if agente=='7' or agente2 == '15':
            venditore = 11
        else:
            venditore = False
        partner_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',codice)])
       
                
        Partner={
            'ref':codice,
            'cod_esenzione_iva':cod_esenzione_iva,
            'name':ragsoc+" "+ragsoc2,
            'agent_id':id_agente,
            'user_id':venditore,
            'credagenti':creditiagenti,
            'meseprimoescluso':meseescluso1,
            'mesesecondoescluso': meseescluso2,
            'giornoescluso': gornoescluso,
            'bloccato':bloccato,
            'moratoria':moratoria,
            #'city':dati_l.get('city',''),
            'email':email,
            'mobile':cell,
            'vat':piva,
            'costumer':True,
            'fiscalcode':codfiscale,
            'phone':tel,
            'category_id':ids_zona,
            'cod_esenzione_iva':id_iva,
            }
        
        if partner_id:
            if type(partner_id)==type([]):  
              partner_id=partner_id[0]

            aggiornati +=1
            ok = self.pool.get('res.partner').write(cr,uid,partner_id,Partner)
            #partner_id=partner_id[0]
            partner_rec = self.pool.get('res.partner').browse(cr,uid,partner_id)
            #import pdb;pdb.set_trace()
            if not partner_rec.property_account_receivable:
             argos=[('code','=','0103001')]
             id_credito = self.pool.get('account.account').search(cr,uid,argos)
             if id_credito:
              argos = [('name', '=','property_account_receivable')] # cerca il pagamento
              ids_field = self.pool.get('ir.model.fields').search(cr,uid,argos)
              if ids_field:
               riga_pagamento = {
                                 'name':'property_account_receivable',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'account.account,'+repr(id_credito[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }
               id_prop_pag = self.pool.get('ir.property').create(cr,uid, riga_pagamento)
            if not partner_rec.property_account_payable:
             argos=[('code','=','0601001')]
             id_credito = self.pool.get('account.account').search(cr,uid,argos)
             #import pdb;pdb.set_trace()
             if id_credito:
              argos = [('name', '=','property_account_payable'),('model','=','res.partner')] # cerca il pagamento
              ids_field = self.pool.get('ir.model.fields').search(cr,uid,argos)
              if ids_field:
               riga_pagamento = {
                                 'name':'property_account_payable',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'account.account,'+repr(id_credito[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }
               id_prop_pag = self.pool.get('ir.property').create(cr,uid, riga_pagamento)
                
                
                
        else:
            inseriti +=1
            partner_id = self.pool.get('res.partner').create(cr,uid,Partner)       
        if partner_id:
          if type(partner_id)==type([]):  
              partner_id=partner_id[0]
          partner_rec = self.pool.get('res.partner').browse(cr,uid,partner_id)
          if len(pagamento)<>0:
            args = [('name', 'ilike',pagamento+'%')] # cerca il pagamento
            ids_pag = self.pool.get('account.payment.term').search(cr,uid, args)
          #import pdb;pdb.set_trace()
          if ids_pag:
            args = [('name', '=','property_payment_term')] # cerca il pagamento
            ids_field = self.pool.get('ir.model.fields').search(cr,uid,args)
            #,('res_id','=','res.partner,'+repr(partner_id))
            if ids_field:
              args = [('name','=','property_payment_term'),('value_reference','=','account.payment.term,'+repr(ids_pag[0])),('res_id','=','res.partner,'+str(partner_id))]
              id_prop_pag =self.pool.get('ir.property').search(cr,uid,args)
              riga_pagamento = {
                                 'name':'property_payment_term',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'account.payment.term,'+repr(ids_pag[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }

              if id_prop_pag:
                  ok = self.pool.get('ir.property').write(cr,uid,id_prop_pag,riga_pagamento)
              else:
                  id_prop_pag = self.pool.get('ir.property').create(cr,uid, riga_pagamento)
                  
          if len(bancaclifor)<>0:          
                args = [('code', '=',bancaclifor)] # cerca il pagamento
                ids_bank = self.pool.get('res.bank').search(cr,uid, args)  
                if ids_bank:
                  riga_banca ={
                         'state': 'bank',
                         'partner_id':partner_id,
                         'bank':ids_bank[0],
                         'acc_number':"001-"+repr(partner_id),
                          }
                
                  if partner_rec.bank_ids:
                      for bank_id in partner_rec.bank_ids:
                          ok = self.pool.get('res.partner.bank').write(cr,uid,bank_id.id,riga_banca)
                  else:                                     
                         id_riga_bank = self.pool.get('res.partner.bank').create(cr,uid, riga_banca)
          #import pdb;pdb.set_trace()
          if listino:
            if listino == 'A':
                args = [('name', 'ilike','Public Pricelist%')] # cerca il listino
                ids_list = self.pool.get('product.pricelist').search(cr,uid, args)
            if listino == 'B':
                args = [('name', 'ilike','LISTINO B%')] # cerca il listino
                ids_list = self.pool.get('product.pricelist').search(cr,uid,args)
            if ids_list:
              
              args = [('name', '=','property_product_pricelist')] # cerca il pagamento
              ids_field = self.pool.get('ir.model.fields').search(cr,uid, args)
              
              if ids_field:
                args = [('name','=','property_product_pricelist'),('value_reference','=','property_product_pricelist,'+repr(ids_list[0])),('res_id','=','res.partner,'+str(partner_id))]
                id_prop_list =self.pool.get('ir.property').search(cr,uid,args)
                 
                #import pdb;pdb.set_trace()
                riga_listino = {
                                 'name':'property_product_pricelist',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'product.pricelist,'+repr(ids_list[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }
                if id_prop_list:
                    
                        ok = self.pool.get('ir.property').write(cr,uid,id_prop_list, riga_listino)
                else:
                    id_prop_list = self.pool.get('ir.property').create(cr,uid, riga_listino)
          city_id = self.pool.get('res.city').search(cr,uid, [('name', '=', localita.title())])
          if city_id:
            citta = self.pool.get('res.city').browse(cr,uid,city_id)[0]
            Indirizzo =  {
                  'partner_id':partner_id,
                  'street': indirizzo,
                  'city':citta['name'],
                  'zip':citta['zip'],
                  'province':citta['province_id'].id,
                  'region':citta['region'].id,       
                  'email':email,
                  'fax':fax,
                  'phone':tel,
                  'mobile':cell, 
                  'name':ragsoc+" "+ragsoc2,
                  }
 
              
          else:
            Indirizzo =  {
                  'partner_id':partner_id,
                  'street': indirizzo,
                  'city':localita.title(),
                  'zip':str(cap),
                  'province':'',
                  'region':'',       
                  'email':email,
                  'fax':fax,
                  'phone':tel,
                  'mobile':cell, 
                  'name':ragsoc+" "+ragsoc2,
                  }
 
                    
          if partner_rec.address:
              for id_addres in partner_rec.address:
                  ok = self.pool.get('res.partner.address').write(cr,uid,[id_addres.id],Indirizzo)
          else:
              id_addres = self.pool.get('res.partner.address').create(cr,uid,Indirizzo)
        
        
     return [inseriti, aggiornati]
 
    def _import_ana_fornitori(self,cr, uid, lines,tipo, context):
     inseriti = 0
     aggiornati = 0
     for line in lines:
            # Mappatura attributi/CSV
        #print line
        line = line.replace('"', '')
        line = line.replace('\n', '')
        line = line.replace(',', '.')
        line = line.split(";")        
     #import pdb;pdb.set_trace()
        #print line[0].strip()
        codice = "%07d" % (int(line[0].strip())) 
        
        if tipo=="F":
            codice=tipo+codice
        ragsoc = line[1].strip()
        ragsoc2 = line[2].strip()
        indirizzo = line[3].strip()
        cap = line[4].strip()
        localita = line[5].strip()
        prov = line[6].strip()
        nazione = line[7].strip()
        tel = line[8].strip()
        if tel.isdigit():
            tel="0"+tel
        fax = line[9].strip()
        if fax.isdigit():
            fax="0"+fax
        cell = line[10].strip()
        if cell.isdigit():
            cell=str(cell)
        codfiscale = line[16].strip()
        piva = str(line[17].strip())    
        pagamento = "%04d" % (int(line[21].strip()))   
        vettore = str(line[22].strip())
        #spedizione = str(line[23].strip())
        porto = str(line[23].strip())
        #zona = "%04d" % (int(line[25].strip()))
        #agente = str(line[26].strip())
        #agente2 = str(line[27].strip())
        #cod_esenzione_iva= str(line[28].strip())
        #codeseconai = line[56].strip()
        #bloccato=line[47].strip()
        #moratoria=line[48].strip()
        #creditiagenti = line[74].strip()
        valuta= str(line[30].strip())
        if line[24].strip():
          bancaclifor = "%07d" % (int(line[24].strip()))
        #if line[31].strip():
        #  bancaazienda = "%07d" % (int(line[31].strip()))
        #meseescluso1 = str(line[32].strip())
        #meseescluso2 = str(line[33].strip())
        #gornoescluso = str(line[34].strip())
        #listino = line[37].strip()
        #codicenazione = line[44].strip()
        #numero_cc =  line[45].strip()
        email = line[52].strip()
        # Controllo PIVA
        if nazione == 'ITA' and len(piva)==9:
            piva = '00'+piva           
        if nazione == 'ITA' and len(piva)==10:
            piva = '0'+piva            
        if not check_vat_it(piva) and nazione == 'ITA':
            piva = False
        else:
            piva = 'IT'+piva            
        if nazione != 'ITA':
            piva = False        
        try:
            codfiscale = int(codfiscale)
        except:
            pass        
        if isinstance(codfiscale,int) or isinstance(codfiscale,long):
           if nazione == 'ITA' and len(str(codfiscale))==9:
             codfiscale = '00'+str(codfiscale)
           elif nazione == 'ITA' and len(str(codfiscale))==10:
             codfiscale = '0'+str(codfiscale)
        if type(codfiscale)<>'str':
          codfiscale = str(codfiscale)
        partner_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',codice)])
        Partner={
            'ref':codice,
            #'cod_esenzione_iva':cod_esenzione_iva,
            'name':ragsoc+" "+ragsoc2,
            #'agent_id':id_agente,
            #'user_id':venditore,
            #'credagenti':creditiagenti,
            #'meseprimoescluso':meseescluso1,
            #'mesesecondoescluso': meseescluso2,
            #'giornoescluso': gornoescluso,
             #'bloccato':bloccato,
            #'moratoria':moratoria,
            #'city':dati_l.get('city',''),
            'email':email,
            'mobile':cell,
            'vat':piva,
            'costumer':False,
            'supplier':True,
            'fiscalcode':codfiscale,
            'phone':tel,
            #'category_id':ids_zona,
            #'cod_esenzione_iva':id_iva,
            }
        
        if partner_id:
            if type(partner_id)==type([]):  
              partner_id=partner_id[0]

            aggiornati +=1
            ok = self.pool.get('res.partner').write(cr,uid,partner_id,Partner)
            #partner_id=partner_id[0]
            partner_rec = self.pool.get('res.partner').browse(cr,uid,partner_id)
            #import pdb;pdb.set_trace()
            if not partner_rec.property_account_receivable:
             argos=[('code','=','0103001')]
             id_credito = self.pool.get('account.account').search(cr,uid,argos)
             if id_credito:
              argos = [('name', '=','property_account_receivable')] # cerca il pagamento
              ids_field = self.pool.get('ir.model.fields').search(cr,uid,argos)
              if ids_field:
               riga_pagamento = {
                                 'name':'property_account_receivable',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'account.account,'+repr(id_credito[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }
               id_prop_pag = self.pool.get('ir.property').create(cr,uid, riga_pagamento)
            if not partner_rec.property_account_payable:
             argos=[('code','=','0601001')]
             id_credito = self.pool.get('account.account').search(cr,uid,argos)
             #import pdb;pdb.set_trace()
             if id_credito:
              argos = [('name', '=','property_account_payable'),('model','=','res.partner')] # cerca il pagamento
              ids_field = self.pool.get('ir.model.fields').search(cr,uid,argos)
              if ids_field:
               riga_pagamento = {
                                 'name':'property_account_payable',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'account.account,'+repr(id_credito[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }
               id_prop_pag = self.pool.get('ir.property').create(cr,uid, riga_pagamento)
                
                
                
        else:
            inseriti +=1
            partner_id = self.pool.get('res.partner').create(cr,uid,Partner)       
        if partner_id:
          if type(partner_id)==type([]):  
              partner_id=partner_id[0]
          partner_rec = self.pool.get('res.partner').browse(cr,uid,partner_id)
          if len(pagamento)<>0:
            args = [('name', 'ilike',pagamento+'%')] # cerca il pagamento
            ids_pag = self.pool.get('account.payment.term').search(cr,uid, args)
          #import pdb;pdb.set_trace()
          if ids_pag:
            args = [('name', '=','property_payment_term')] # cerca il pagamento
            ids_field = self.pool.get('ir.model.fields').search(cr,uid,args)
            #,('res_id','=','res.partner,'+repr(partner_id))
            if ids_field:
              args = [('name','=','property_payment_term'),('value_reference','=','account.payment.term,'+repr(ids_pag[0])),('res_id','=','res.partner,'+str(partner_id))]
              id_prop_pag =self.pool.get('ir.property').search(cr,uid,args)
              riga_pagamento = {
                                 'name':'property_payment_term',
                                 'type':'many2one',
                                 'fields_id':ids_field[0],
                                 'company_id':1,
                                 'value_reference':'account.payment.term,'+repr(ids_pag[0]),
                                 'res_id':'res.partner,'+repr(partner_id),
                                 }

              if id_prop_pag:
                  ok = self.pool.get('ir.property').write(cr,uid,id_prop_pag,riga_pagamento)
              else:
                  id_prop_pag = self.pool.get('ir.property').create(cr,uid, riga_pagamento)
                  
          if len(bancaclifor)<>0:          
                args = [('code', '=',bancaclifor)] # cerca il pagamento
                ids_bank = self.pool.get('res.bank').search(cr,uid, args)  
                if ids_bank:
                  riga_banca ={
                         'state': 'bank',
                         'partner_id':partner_id,
                         'bank':ids_bank[0],
                         'acc_number':"001-"+repr(partner_id),
                          }
                
                  if partner_rec.bank_ids:
                      for bank_id in partner_rec.bank_ids:
                          ok = self.pool.get('res.partner.bank').write(cr,uid,bank_id.id,riga_banca)
                  else:                                     
                         id_riga_bank = self.pool.get('res.partner.bank').create(cr,uid, riga_banca)
          #import pdb;pdb.set_trace()
          # INSERISCE L'INDIRIZZO BASE
          city_id = self.pool.get('res.city').search(cr,uid, [('name', '=', localita.title())])
          if city_id:
            citta = self.pool.get('res.city').browse(cr,uid,city_id)[0]
            Indirizzo =  {
                  'partner_id':partner_id,
                  'street': indirizzo,
                  'city':citta['name'],
                  'zip':citta['zip'],
                  'province':citta['province_id'].id,
                  'region':citta['region'].id,       
                  'email':email,
                  'fax':fax,
                  'phone':tel,
                  'mobile':cell, 
                  'name':ragsoc+" "+ragsoc2,
                  }
 
              
          else:
            Indirizzo =  {
                  'partner_id':partner_id,
                  'street': indirizzo,
                  'city':localita.title(),
                  'zip':str(cap),
                  'province':'',
                  'region':'',       
                  'email':email,
                  'fax':fax,
                  'phone':tel,
                  'mobile':cell, 
                  'name':ragsoc+" "+ragsoc2,
                  }
 
                    
          if partner_rec.address:
              for id_addres in partner_rec.address:
                  ok = self.pool.get('res.partner.address').write(cr,uid,[id_addres.id],Indirizzo)
          else:
              id_addres = self.pool.get('res.partner.address').create(cr,uid,Indirizzo)
        
        
     return [inseriti, aggiornati]

 
 
 
 

    
    def run_import(self, cr, uid, ids, automatic=False, use_new_cursor=False, context=None):
      #pool = pooler.get_pool(cr.dbname)  
      #import pdb;pdb.set_trace()
      import_data = self.browse(cr, uid, ids)[0]
      cerca =[]
      fileobj = TemporaryFile('w+')
      fileobj.write(base64.decodestring(import_data.data))
      fileobj.seek(0)
      lines = fileobj.readlines()
      testo_log = """Inizio procedura di Importazione""" + time.ctime() + '\n'
      error = False
      nome =''      
      #percorso = '/home/openerp/filecsv'
      #import pdb;pdb.set_trace()
      if use_new_cursor:
        use_new_cursor= use_new_cursor[0]         
        cr = pooler.get_db(use_new_cursor).cursor()
      # elenco_csv = os.listdir(percorso)
      res = False
      try:
        if use_new_cursor:
            cr = pooler.get_db(use_new_cursor).cursor()
        if import_data.clienti_base:
                pass              
                res = self._import_ana_base(cr, uid, lines,"C", context)
        if import_data.fornitori_base:
                pass              
                res = self._import_ana_fornitori(cr, uid, lines,"F", context)
                
        if import_data.banche:
                pass
                res = self._import_banche(cr, uid, lines, context)
        if import_data.des_dive_cli:
                res = self._import_desdive(cr, uid, lines, context)
          
        if use_new_cursor:
                    cr.commit()
          
          
        if res:  
                    testo_log = testo_log + " Inseriti " + str(res[0]) + " Aggiornati " + str(res[1]) + "  \n"
        else:
                testo_log = testo_log + " File non riconosciuto  " + codfor[0] + " non trovato  \n"
      
                testo_log = testo_log + " Operazione Teminata  alle " + time.ctime() + "\n"
                #invia e-mail
                type_ = 'plain'
                tools.email_send('OpenErp@mainettiomaf.it',
                       ['g.dalo@cgsoftware.it'],
                       'Importazione da Altre Procedure',
                       testo_log,
                       subtype=type_,
                       )
      finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        

        
      return {'type': 'ir.actions.act_window_close'}  
  
    def run_auto_import(self, cr, uid,ids, automatic=False, use_new_cursor=False, context=None):
        """
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        """
        #import pdb;pdb.set_trace()
        use_new_cursor=cr.dbname,
        threaded_calculation = threading.Thread(target=self.run_import, args=(cr, uid,ids, automatic, use_new_cursor, context))        
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}  

  
import_anagrafiche()


