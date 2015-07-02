window.google=window.google||{};google.maps=google.maps||{};(function(){function getScript(src){document.write('<'+'script src="'+src+'"'+' type="text/javascript"><'+'/script>');}
var modules=google.maps.modules={};google.maps.__gjsload__=function(name,text){modules[name]=text;};google.maps.Load=function(apiLoad){delete google.maps.Load;apiLoad([null,[[["http://mt0.googleapis.com/vt?lyrs=m@146\u0026src=api\u0026hl=en-US\u0026","http://mt1.googleapis.com/vt?lyrs=m@146\u0026src=api\u0026hl=en-US\u0026"]],[["http://khm0.googleapis.com/kh?v=80\u0026hl=en-US\u0026","http://khm1.googleapis.com/kh?v=80\u0026hl=en-US\u0026"],null,null,null,1],[["http://mt0.googleapis.com/vt?lyrs=h@146\u0026src=api\u0026hl=en-US\u0026","http://mt1.googleapis.com/vt?lyrs=h@146\u0026src=api\u0026hl=en-US\u0026"],null,null,"imgtp=png32\u0026"],[["http://mt0.googleapis.com/vt?lyrs=t@126,r@146\u0026src=api\u0026hl=en-US\u0026","http://mt1.googleapis.com/vt?lyrs=t@126,r@146\u0026src=api\u0026hl=en-US\u0026"]],null,[[null,0,7,7,[[[330000000,1246050000],[386200000,1293600000]],[[366500000,1297000000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026"]],[null,0,8,9,[[[330000000,1246050000],[386200000,1279600000]],[[345000000,1279600000],[386200000,1286700000]],[[348900000,1286700000],[386200000,1293600000]],[[354690000,1293600000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026"]],[null,0,10,19,[[[329890840,1246055600],[386930130,1284960940]],[[344646740,1284960940],[386930130,1288476560]],[[350277470,1288476560],[386930130,1310531620]],[[370277730,1310531620],[386930130,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026"]],[null,3,7,7,[[[330000000,1246050000],[386200000,1293600000]],[[366500000,1297000000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026"]],[null,3,8,9,[[[330000000,1246050000],[386200000,1279600000]],[[345000000,1279600000],[386200000,1286700000]],[[348900000,1286700000],[386200000,1293600000]],[[354690000,1293600000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026"]],[null,3,10,null,[[[329890840,1246055600],[386930130,1284960940]],[[344646740,1284960940],[386930130,1288476560]],[[350277470,1288476560],[386930130,1310531620]],[[370277730,1310531620],[386930130,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026"]]],[["http://cbk0.google.com/cbk?","http://cbk1.google.com/cbk?"]],[["http://khmdb0.googleapis.com/kh?v=36\u0026hl=en-US\u0026","http://khmdb1.googleapis.com/kh?v=36\u0026hl=en-US\u0026"]],[["http://mt0.googleapis.com/mapslt?hl=en-US\u0026","http://mt1.googleapis.com/mapslt?hl=en-US\u0026"]],[["http://mt0.googleapis.com/mapslt/ft?hl=en-US\u0026","http://mt1.googleapis.com/mapslt/ft?hl=en-US\u0026"]]],["en-US","US",null,0,null,"http://maps.google.com","http://maps.gstatic.com/intl/en_us/mapfiles/","http://gg.google.com","https://maps.googleapis.com","http://maps.googleapis.com"],["http://maps.gstatic.com/intl/en_us/mapfiles/api-3/4/4a","3.4.4a"],[936849974],1,null,null,null,null,0,"",null,null,0],loadScriptTime);};var loadScriptTime=(new Date).getTime();getScript("http://maps.gstatic.com/intl/en_us/mapfiles/api-3/4/4a/main.js");})();var ol_map=(function()
{var location_array=new Array();var loc_map=new Array();var layer_array=new Array();var style_array=new Array();marker_list={};loc_map[0]={};loc_map[1]={};var hover_control_id=0;return{init:function(loc_list,minimap)
{location_array=ol_map.build_location_array(loc_list);lng=location_array[0][0];lat=location_array[0][1];if(minimap==null)
{map_id=0;div_map_id='displaymap';}
else
{ol_map.init(loc_list);map_id=1;hover_control_id=1;div_map_id='minimap';}
var WGS84=new OpenLayers.Projection("EPSG:4326");ol_map.build_base_layer(div_map_id,map_id);var lonlat=new OpenLayers.LonLat(lng,lat).transform(new OpenLayers.Projection("EPSG:4326"),new OpenLayers.Projection("EPSG:900913"));loc_map[map_id].map.setCenter(lonlat);loc_map[map_id].map.zoomTo(14);bounds=place_coupon_markers(loc_map[map_id].map,location_array);if(bounds.left==bounds.right)
{bounds.top-=700;bounds.bottom+=700;bounds.right+=700;bounds.left-=700;}
ol_map.custom_zoom(loc_map[map_id].map,bounds,'market');if(!loc_map[map_id].map.getCenter()){loc_map[map_id].map.zoomToMaxExtent()}},build_base_layer:function(div_id,map_id)
{if(typeof div_id=='undefined')
{div_id='displaymap';}
if(typeof map_id=='undefined')
{map_id=0;}
ol_map.market_map_setup(loc_map[map_id]);OpenLayers.ImgPath='/media/images/'
var WGS84=new OpenLayers.Projection("EPSG:4326");var maxExtent=new OpenLayers.Bounds(-20037508,-20037508,20037508,20037508),restrictedExtent=maxExtent.clone(),maxResolution=156543.0339;var options={'units':"m",'numZoomLevels':20,'controls':[new OpenLayers.Control.Navigation()],'projection':new OpenLayers.Projection("EPSG:900913"),'displayProjection':WGS84,'maxResolution':maxResolution,'maxExtent':maxExtent,'restrictedExtent':restrictedExtent,'buffer':0,'theme':null,'autoPan':true};loc_map[map_id].map=new OpenLayers.Map(div_id,options);loc_map[map_id].layers.base=new OpenLayers.Layer.Google("Google",{});loc_map[map_id].map.addLayer(loc_map[map_id].layers.base);loc_map[map_id].layers.base.poweredBy='gg_watermark';var panel=new OpenLayers.Control.Panel();panel.addControls([new ol_map.buildZoomControl(options)]);loc_map[map_id].map.addControl(panel);panel.activate();},buildZoomControl:function(options)
{this.control=new OpenLayers.Control.PanZoomBar(options);OpenLayers.Util.extend(this.control,{draw:function(px){OpenLayers.Control.prototype.draw.apply(this,arguments);px=this.position.clone();this.buttons=[];var sz=new OpenLayers.Size(18,18);var centered=new OpenLayers.Pixel(0,px.y);this._addButton("zoomin","map_pointers/zoom-in.png",centered.add(4,0),sz);this._addButton("zoomout","map_pointers/zoom-out.png",centered.add(4,22),sz);return this.div;}});return this.control;},build_location_array:function(list)
{var nested_array=new Array();for(var i=0;i<list.length;i++)
{nested_array[i]=new Array();if(list[i].length>1)
{nested_array[i][0]=list[i][0];nested_array[i][1]=list[i][1];if(list[i].length==3)
{nested_array[i][2]=list[i][2];}
else
{nested_array[i][2]='';}}}
return nested_array},setMarkerToCenter:function(marker)
{var id=marker.match(/\d+/g)-1;lng=location_array[id][0];lat=location_array[id][1];var lonlat=new OpenLayers.LonLat(lng,lat).transform(new OpenLayers.Projection("EPSG:4326"),new OpenLayers.Projection("EPSG:900913"));loc_map[hover_control_id].setCenter(lonlat);return},market_map_setup:function(map_obj)
{map_obj.map=null;map_obj.layers={};map_obj.wkt_f=new OpenLayers.Format.WKT();map_obj.get_ewkt=function(feat){return'SRID=900913;'+map_obj.wkt_f.write(feat);}
map_obj.read_wkt=function(wkt)
{return map_obj.wkt_f.read(wkt);}
map_obj.write_wkt=function(feat)
{document.getElementById('id_geom').value=map_obj.get_ewkt(feat);}},build_markets_map:function()
{ol_map.build_base_layer();ol_map.load_doc();},build_geoms_for_single_market:function(markets,interactive)
{var bounds=new OpenLayers.Bounds();var this_bounds;var myLabel;var geom_vector_data;var layer_array=new Array();var zoom_level='market';var style_index;var geom_data=markets.replace(/['"]/g,'');var geom_array=geom_data.split('|');ol_map.build_base_layer();var color_list=[["#f9b7e8","#cb74b4"],["#de638f","#cb74b4"],["#ae50bf","#cb74b4"],["#d57bbd","#cb74b4"],["#c66aad","#cb74b4"],["#f9b7e8","#cb74b4"],["#e799d2","#cb74b4"],["#dd8fc8","#cb74b4"],["#d57bbd","#cb74b4"],["#c66aad","#cb74b4"]]
for(var i=0;i<geom_array.length;i++)
{style_index=i.toString().substring(i.toString().length-1)
geom_array[i]=geom_array[i].split(';');myLabel=geom_array[i][1];style_array[i]=new OpenLayers.StyleMap({"default":new OpenLayers.Style({pointRadius:"${type}",fillColor:color_list[style_index][0].toString(),strokeColor:color_list[style_index][1].toString(),strokeWidth:1.3,graphicZIndex:1,fillOpacity:0.7,label:myLabel,fontColor:"#382282",fontSize:12,fontWeight:"600",labelAlign:"cm",labelXOffset:i,labelYOffset:i-2})});if(geom_array[i][0]!='')
{layer_array[i]=new OpenLayers.Layer.Vector("Layer_"+i,{styleMap:style_array[i],LID:geom_array[i][2]});geom_data1=geom_array[i][0];geom_vector_data=loc_map[0].read_wkt(geom_data1);layer_array[i].addFeatures([geom_vector_data]);this_bounds=geom_vector_data.geometry.getBounds();bounds.extend(this_bounds);loc_map[0].map.addLayers([layer_array[i]])}}
if(interactive==true)
{var highlightCtrl=new OpenLayers.Control.SelectFeature(layer_array,{hover:true,highlightOnly:true,renderIntent:"temporary"});var selectCtrl=new OpenLayers.Control.SelectFeature(layer_array,{clickout:true,click:true,single:true,onSelect:function(e){window.location="/"+e.layer.LID.toString().replace(/\s/g,"").replace(' ','-')+'/';}});loc_map[0].map.addControl(highlightCtrl);loc_map[0].map.addControl(selectCtrl);highlightCtrl.activate();selectCtrl.activate();}
var url_path=window.location.href.toLowerCase();if(url_path.indexOf('hawaii')>1||this_bounds.toString().replace(/[^0-9,.]/g,'').toString().split(',')[0]>19500000.227845)
{if(url_path.indexOf('hawaii')>1||this_bounds.toString().replace(/[^0-9,.]/g,'').toString().split(',')[1]<2450000)
{zoom_level='hawaii';}}
ol_map.custom_zoom(loc_map[0].map,bounds,zoom_level);if(!loc_map[0].map.getCenter()){loc_map[0].map.zoomToMaxExtent()}},custom_zoom:function(map,bounds,type)
{if(typeof type=="undefined"){type="default";}
switch(type)
{case"hawaii":myZoom=7;lonCenter=-157.8583333;latCenter=21.3069444;break;case"market":map.zoomToExtent(bounds);return;case"continent":default:myZoom=3;lonCenter=-110.683333;latCenter=50.033333;break;}
myPoint=new OpenLayers.Geometry.Point(lonCenter,latCenter);OpenLayers.Projection.transform(myPoint,map.displayProjection,map.getProjectionObject());map.setCenter(new OpenLayers.LonLat(myPoint.x,myPoint.y),myZoom);return;},build_country_map:function()
{var bounds=new OpenLayers.Bounds();var this_bounds;var geom_data=document.getElementById('id_geom').value.replace(/['"]/g,'');var geom_array=geom_data.split('|');var layer_array=new Array();var geom_vector_data;for(var i=0;i<geom_array.length;i++)
{geom_array[i]=geom_array[i].split(';');style_array[i]=new OpenLayers.StyleMap({"default":new OpenLayers.Style({pointRadius:"${type}",fillColor:'#dd8fc8',strokeColor:'#cb74b4',strokeWidth:1.25,graphicZIndex:1,fillOpacity:0.2,label:geom_array[i][1],fontColor:'#fbcf79',fontSize:1,fontWeight:"000"})});layer_array[i]=new OpenLayers.Layer.Vector("Layer_"+i,{styleMap:style_array[i],LID:geom_array[i][1],'rendererOptions':{yOrdering:false,zIndexing:true}});loc_map[0].map.addLayers([layer_array[i]]);if(geom_array[i][0]!='')
{geom_data1=geom_array[i][0];geom_vector_data=loc_map[0].read_wkt(geom_data1);layer_array[i].addFeatures([geom_vector_data]);this_bounds=geom_vector_data.geometry.getBounds();bounds.extend(this_bounds);}}
var highlightCtrl=new OpenLayers.Control.SelectFeature(layer_array,{hover:true,highlightOnly:true,renderIntent:"temporary"});var selectCtrl=new OpenLayers.Control.SelectFeature(layer_array,{clickout:true,click:true,single:true,onSelect:function(e){window.location="/map/"+e.layer.LID.toString().replace(/\s/g,"").replace(' ','-')+'/';}});loc_map[0].map.addControl(highlightCtrl);loc_map[0].map.addControl(selectCtrl);highlightCtrl.activate();selectCtrl.activate();place_markers(loc_map[0].map);ol_map.custom_zoom(loc_map[0].map,bounds,'continent');if(!loc_map[0].map.getCenter()){loc_map[0].map.zoomToMaxExtent()}},load_doc:function()
{var xmlhttp;if(window.XMLHttpRequest)
{xmlhttp=new XMLHttpRequest();}
else
{xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");}
xmlhttp.onreadystatechange=function()
{if(xmlhttp.readyState==4&&xmlhttp.status==200)
{document.getElementById("id_geom").value=xmlhttp.responseText;ol_map.build_country_map();}}
xmlhttp.open("GET","/media/data/state_geometries.json",true);xmlhttp.send();},create_market_list:function(list)
{marker_list=list;}};})();function place_coupon_markers(map,marker_array)
{marker_style_array=new Array();marker_stylemap_array=new Array();marker_layers=new Array();var features=[];for(i=0;i<=10;i+=1)
{g_height=25;g_width=21;g_suffix='_'+i.toString()+'.png';marker_style_array[i]=new OpenLayers.Style({'externalGraphic':'/media/images/map_pointers/map_pointer'+g_suffix,'graphicHeight':g_height,'graphicWidth':g_width});marker_stylemap_array[i]=new OpenLayers.StyleMap({'default':marker_style_array[i]});if(i>=marker_array.length)
{break;}}
for(i=1;i<=marker_array.length;i++)
{marker_name="Markers_"+i.toString();marker_layers[i]=new OpenLayers.Layer.Vector(marker_name,{'styleMap':marker_stylemap_array[i]});features=[];myPoint=new OpenLayers.Geometry.Point(marker_array[i-1][0],marker_array[i-1][1]);OpenLayers.Projection.transform(myPoint,map.displayProjection,map.getProjectionObject());features.push(new OpenLayers.Feature.Vector(myPoint));marker_layers[i].addFeatures(features);map.addLayer(marker_layers[i]);}
layer_bounds=null;for(i=1;i<marker_layers.length;i++)
{if(layer_bounds==null)
{layer_bounds=marker_layers[i].getDataExtent();}
else
{layer_bounds.extend(marker_layers[i].getDataExtent());}}
return layer_bounds;}
function place_markers(map)
{var WGS84=new OpenLayers.Projection("EPSG:4326");marker_array=new Array();marker_style_array=new Array();marker_stylemap_array=new Array();marker_layers=new Array();marker_array=ol_map.build_location_array(marker_list);marker_style_array[0]=new OpenLayers.Style({'externalGraphic':'/media/images/map_pointers/markerstar.png','graphicHeight':8,'graphicWidth':8});marker_stylemap_array[0]=new OpenLayers.StyleMap({'default':marker_style_array[0]});var markers=new OpenLayers.Layer.Vector("Markers",{'styleMap':marker_stylemap_array[0]});var features=[];for(i=0;i<marker_array.length;i++)
{myPoint=new OpenLayers.Geometry.Point(marker_array[i][0],marker_array[i][1]);OpenLayers.Projection.transform(myPoint,map.displayProjection,map.getProjectionObject());features.push(new OpenLayers.Feature.Vector(myPoint));}
markers.addFeatures(features);map.addLayer(markers);return markers.getDataExtent();}