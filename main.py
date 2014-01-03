#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import cgi
import os
import datetime
import logging

from google.appengine.ext.webapp import util
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import images
from google.appengine.api import memcache
from django.utils import simplejson

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.render_form()

    def render_form(self):
        from google.appengine.api import memcache
        
        template_values = {
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class Search(webapp.RequestHandler):
    def get(self):
        import bottlenose
        import xml.dom.minidom as minidom
        from xml.dom.minidom import parse, parseString
        
        resultsArry = ()
        amazon = bottlenose.Amazon('', '', '')
        if self.request.get('page') == '':
            pageNum=1
        else:
            pageNum = int(self.request.get('page'))
            
        keywords = self.request.get('keywords')
        
        response = amazon.ItemSearch(Keywords=keywords,ResponseGroup="ItemAttributes,Images",SearchIndex="All", Condition="New", ItemPage=pageNum)

        responseXML = parseString(response)
        #results = responseXML.getElementsByTagName("Item")
        #print type(results)
        productList = []
        productDict = {}
        
        #prodResults = [data.childNodes.item(0).data for data in results]
        for items in responseXML.getElementsByTagName("Items"):
            for results in items.getElementsByTagName("TotalResults"):
                TotalResults = results.childNodes.item(0).data
                
            for attrs in items.getElementsByTagName("Item"):
                for manuf in attrs.getElementsByTagName("Manufacturer"):
                    productDict["manuf"] = manuf.childNodes.item(0).data
                    #print manuf.childNodes.item(0).data
                
                for title in attrs.getElementsByTagName("Title"):
                    productDict["title"] = title.childNodes.item(0).data
                    
                for model in attrs.getElementsByTagName("Model"):
                    productDict["model"] = model.childNodes.item(0).data
                    
                for prodGroup in attrs.getElementsByTagName("ProductGroup"):
                    productDict["group"] = prodGroup.childNodes.item(0).data
                
                for ASIN in attrs.getElementsByTagName("ASIN"):
                    productDict["ASIN"] = ASIN.childNodes.item(0).data
                
                for listPrice in attrs.getElementsByTagName("ListPrice"):
                    for formatPrice in attrs.getElementsByTagName("FormattedPrice"):
                        productDict["listPrice"] = formatPrice.childNodes.item(0).data
                    
                for imageThumb in attrs.getElementsByTagName("ImageSets"):
                    for url in imageThumb.getElementsByTagName("ThumbnailImage"):
                        for dest in url.getElementsByTagName("URL"):
                            productDict["imageThumb"] = dest.childNodes.item(0).data
                            break
                        break    
                    break
                    
                productList.append(productDict)
                productDict = {}
                
        #print len(productList)
        # This is the structure we need. Each product is a different row
        #'searchResults': [{'first':"michael","last":"thamm"},
        #                  {'first':"jim","last":"smith"}],
        
        # need to send the next page to the template
        # Have to check TotalResults to make sure more than 10 were returned. 
        # If less than 10, no other page is needed. 
        #nextPageNum should then be 0
        if int(TotalResults) > 10:
            nextPageNum = pageNum + 1
            if pageNum > 0:
                prevPageNum = pageNum - 1
            else:
                prevPageNum = 0
        else:
            nextPageNum=0
            prevPageNum=0

        template_values = {

            'searchResults': productList,
            'kw':keywords,
            'nextPage': nextPageNum,
            'prevPage': prevPageNum,
            'currPage': pageNum,
        }
        path = os.path.join(os.path.dirname(__file__), 'results.html')
        self.response.out.write(template.render(path, template_values))
        
class Details(webapp.RequestHandler):
    def get(self):
        import bottlenose
        import xml.dom.minidom as minidom
        from xml.dom.minidom import parse, parseString
        from google.appengine.api import memcache
        
        resultsArry = ()
        listings = () # holds an array of the dictionary offer listings
        asin = self.request.get('asin')
        amazon = bottlenose.Amazon('', '', '')
        response = amazon.ItemLookup(ItemId=asin, ResponseGroup= "Medium,Images,OfferFull")
        #response = amazon.ItemSearch(Keywords=self.request.get('keywords'),ResponseGroup="ItemAttributes,Images",SearchIndex="All")

        responseXML = parseString(response)
        #results = responseXML.getElementsByTagName("Item")
        #print type(results)
        productDet = []
        productDict = {}
        
        #prodResults = [data.childNodes.item(0).data for data in results]
        for items in responseXML.getElementsByTagName("Items"):
            
            for attrs in items.getElementsByTagName("Item"):
                for manuf in attrs.getElementsByTagName("Manufacturer"):
                    productDict["manuf"] = manuf.childNodes.item(0).data
                    #print manuf.childNodes.item(0).data
                    
                for prodGroup in attrs.getElementsByTagName("ProductGroup"):
                    productDict["group"] = prodGroup.childNodes.item(0).data
                    
                for title in attrs.getElementsByTagName("Title"):
                    productDict["title"] = title.childNodes.item(0).data
                
                for model in attrs.getElementsByTagName("Model"):
                    productDict["model"] = model.childNodes.item(0).data

                for ASIN in attrs.getElementsByTagName("ASIN"):
                    productDict["ASIN"] = ASIN.childNodes.item(0).data
                
                for listPrice in attrs.getElementsByTagName("ListPrice"):
                    for formatPrice in listPrice.getElementsByTagName("FormattedPrice"):
                        productDict["listPrice"] = formatPrice.childNodes.item(0).data
                
                for edReviews in attrs.getElementsByTagName("EditorialReviews"):
                    for edReview in edReviews.getElementsByTagName("EditorialReview"):
                        for desc in edReview.getElementsByTagName("Content"):
                            productDict["source"] = desc.childNodes.item(0).data
                            
                        for desc in edReview.getElementsByTagName("Content"):
                            productDict["desc"] = desc.childNodes.item(0).data
                
                for imageLarge in attrs.getElementsByTagName("ImageSets"):
                    for url in imageLarge.getElementsByTagName("LargeImage"):
                        for dest in url.getElementsByTagName("URL"):
                            productDict["imageLarge"] = dest.childNodes.item(0).data
                            break
                        break
                    break
                    
                productDet.append(productDict)
                productDict = {}
                
        listingArry=[]
        listingDict ={}
        for offer in responseXML.getElementsByTagName("Offers"):
            for merchant in responseXML.getElementsByTagName("Offer"):
                #<OfferListing>  Same level
                #    <OfferListingId>
                #    <Price>
                #        <FormattedPrice>
                for name in merchant.getElementsByTagName("Merchant"):
                    for merchname in name.getElementsByTagName("Name"):
                        listingDict["merchant"] = merchname.childNodes.item(0).data
                        
                for OfferListing in merchant.getElementsByTagName("OfferListing"):
                    for OfferListingId in OfferListing.getElementsByTagName("OfferListingId"):
                        listingDict["OfferListingId"] = OfferListingId.childNodes.item(0).data
                    for Price in OfferListing.getElementsByTagName("Price"):
                        for FormattedPrice in Price.getElementsByTagName("FormattedPrice"):
                            listingDict["FormattedPrice"] = FormattedPrice.childNodes.item(0).data
                       

        listingArry.append(listingDict)
           
        template_values = {
            'productDetails': productDet,
            'listings' : listingArry,
        }
        path = os.path.join(os.path.dirname(__file__), 'detail.html')
        self.response.out.write(template.render(path, template_values))
        
class AddToCart(webapp.RequestHandler):
    def get(self):
        import bottlenose
        import xml.dom.minidom as minidom
        from xml.dom.minidom import parse, parseString
        from google.appengine.api import memcache
        
        cartExists = '1'
        #checkMemCache for the cart by checking for IP/Host
        ipAddr = self.request.environ['HTTP_HOST']
        cartData = memcache.get(ipAddr)
        if cartData is None: #IP doesn't exist - Create the cart
            cartExists = '0'
            
            cartData = { "ip":ipAddr,"cartId":"CARTID" } #create the cache
            memcache.add(ipAddr, cartData, 600)
        
        # Now add the item with a CartAdd command
        # The memcache is just holding the pointer to the 
        # remote cart.
                
        resultsArry = ()
        listings = () # holds an array of the dictionary offer listings
        
        OfferListingId = self.request.get('listid')

        self.response.out.write(cartExists)

class ViewCart(webapp.RequestHandler):
    def get(self):
        
        import bottlenose
        import xml.dom.minidom as minidom
        from xml.dom.minidom import parse, parseString
        from google.appengine.api import memcache
        
        cartcontents = ''
        
        ipAddr = self.request.environ['HTTP_HOST']
        cartData = memcache.get(ipAddr)
        
        if cartData != None: #IP doesn't exist - Create the cart
            cartcontents = [{'productID':'ABCD','desc':'Description goes here','qty':1,'price':'$2.00'}]
                
        template_values = {
            'cartContents' : cartcontents
        }
        path = os.path.join(os.path.dirname(__file__), 'cart.html')
        self.response.out.write(template.render(path, template_values))

class CartExists(webapp.RequestHandler):
    def get(self):
        from google.appengine.api import memcache
        cartExists = '0'
        #checkMemCache for the cart by checking for IP/Host
        ipAddr = self.request.environ['HTTP_HOST']
        cartData = memcache.get(ipAddr)
        if cartData != None: #IP doesn't exist - Create the cart
            cartExists = '1'

        self.response.out.write(cartExists)    

class DeleteFromCart(webapp.RequestHandler):
    def get(self):
        from google.appengine.api import memcache
        cartExists = '0'
        #checkMemCache for the cart by checking for IP/Host
        ipAddr = self.request.environ['HTTP_HOST']
        cartData = memcache.get(ipAddr)
        if cartData != None: #IP doesn't exist - Create the cart
            cartExists = '1'
        # Have to check the total items in the cart from Amazon API response
        self.response.out.write(cartExists)  
        
class Image (webapp.RequestHandler):
    def get(self):
        greeting = db.get(self.request.get("img_id"))
        if greeting.avatar:
          self.response.headers['Content-Type'] = "image/png"
          self.response.out.write(greeting.avatar)
        else:
          self.response.out.write("No image")
          
          
class ClearCache (webapp.RequestHandler):
    def get(self):
        from google.appengine.api import memcache
        self.response.out.write( memcache.flush_all())
        self.redirect("/")

class NotFoundPageHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        self.response.out.write('Page Not Found - 404!')

          
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/search',Search),
                                        ('/details',Details),
                                        ('/addtocart',AddToCart),
                                        ('/viewcart',ViewCart),
                                        ('/cartexists',CartExists),
                                        ('/deletefromcart',DeleteFromCart),
                                        ('/clearcache',ClearCache),
                                        ('/img',Image),
                                        ('/.*', NotFoundPageHandler)],
                                         debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
