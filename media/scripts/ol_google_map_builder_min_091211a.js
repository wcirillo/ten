
window.google=window.google||{};google.maps=google.maps||{};(function(){function getScript(src){document.write('<'+'script src="'+src+'"'+' type="text/javascript"><'+'/script>');}
var modules=google.maps.modules={};google.maps.__gjsload__=function(name,text){modules[name]=text;};google.maps.Load=function(apiLoad){delete google.maps.Load;apiLoad([null,[[["http://mt0.googleapis.com/vt?lyrs=m@146\u0026src=api\u0026hl=en-US\u0026","http://mt1.googleapis.com/vt?lyrs=m@146\u0026src=api\u0026hl=en-US\u0026"]],[["http://khm0.googleapis.com/kh?v=80\u0026hl=en-US\u0026","http://khm1.googleapis.com/kh?v=80\u0026hl=en-US\u0026"],null,null,null,1],[["http://mt0.googleapis.com/vt?lyrs=h@146\u0026src=api\u0026hl=en-US\u0026","http://mt1.googleapis.com/vt?lyrs=h@146\u0026src=api\u0026hl=en-US\u0026"],null,null,"imgtp=png32\u0026"],[["http://mt0.googleapis.com/vt?lyrs=t@126,r@146\u0026src=api\u0026hl=en-US\u0026","http://mt1.googleapis.com/vt?lyrs=t@126,r@146\u0026src=api\u0026hl=en-US\u0026"]],null,[[null,0,7,7,[[[330000000,1246050000],[386200000,1293600000]],[[366500000,1297000000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026"]],[null,0,8,9,[[[330000000,1246050000],[386200000,1279600000]],[[345000000,1279600000],[386200000,1286700000]],[[348900000,1286700000],[386200000,1293600000]],[[354690000,1293600000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026"]],[null,0,10,19,[[[329890840,1246055600],[386930130,1284960940]],[[344646740,1284960940],[386930130,1288476560]],[[350277470,1288476560],[386930130,1310531620]],[[370277730,1310531620],[386930130,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1.13\u0026hl=en-US\u0026"]],[null,3,7,7,[[[330000000,1246050000],[386200000,1293600000]],[[366500000,1297000000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026"]],[null,3,8,9,[[[330000000,1246050000],[386200000,1279600000]],[[345000000,1279600000],[386200000,1286700000]],[[348900000,1286700000],[386200000,1293600000]],[[354690000,1293600000],[386200000,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026"]],[null,3,10,null,[[[329890840,1246055600],[386930130,1284960940]],[[344646740,1284960940],[386930130,1288476560]],[[350277470,1288476560],[386930130,1310531620]],[[370277730,1310531620],[386930130,1320034790]]],["http://mt0.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026","http://mt1.gmaptiles.co.kr/mt?v=kr1p.12\u0026hl=en-US\u0026"]]],[["http://cbk0.google.com/cbk?","http://cbk1.google.com/cbk?"]],[["http://khmdb0.googleapis.com/kh?v=36\u0026hl=en-US\u0026","http://khmdb1.googleapis.com/kh?v=36\u0026hl=en-US\u0026"]],[["http://mt0.googleapis.com/mapslt?hl=en-US\u0026","http://mt1.googleapis.com/mapslt?hl=en-US\u0026"]],[["http://mt0.googleapis.com/mapslt/ft?hl=en-US\u0026","http://mt1.googleapis.com/mapslt/ft?hl=en-US\u0026"]]],["en-US","US",null,0,null,"http://maps.google.com","http://maps.gstatic.com/intl/en_us/mapfiles/","http://gg.google.com","https://maps.googleapis.com","http://maps.googleapis.com"],["http://maps.gstatic.com/intl/en_us/mapfiles/api-3/4/4a","3.4.4a"],[936849974],1,null,null,null,null,0,"",null,null,0],loadScriptTime);};var loadScriptTime=(new Date).getTime();getScript("http://maps.gstatic.com/intl/en_us/mapfiles/api-3/4/4a/main.js");})();var ol_map=(function()
{var location_array=new Array();var loc_map=new Array();var layer_array=new Array();var whole_market_layer;var style_array=new Array();var selected_geoms_array=new Array();var file_prefix;marker_list={};loc_map[0]={};loc_map[1]={};options_dict={minZoomLevel:7,maxZoomLevel:17}
var hover_control_id=0;return{build_location_map:function(loc_list,minimap)
{location_array=ol_map.build_location_array(loc_list);lng=location_array[0][0];lat=location_array[0][1];if(minimap==null)
{map_id=0;div_map_id='displaymap';}
else
{ol_map.build_location_map(loc_list);map_id=1;hover_control_id=1;div_map_id='minimap';}
options_dict={minZoomLevel:7,maxZoomLevel:19}
var WGS84=new OpenLayers.Projection("EPSG:4326");ol_map.build_base_layer(div_map_id,map_id);var lonlat=new OpenLayers.LonLat(lng,lat).transform(new OpenLayers.Projection("EPSG:4326"),new OpenLayers.Projection("EPSG:900913"));loc_map[map_id].map.setCenter(lonlat);loc_map[map_id].map.zoomTo(14);bounds=place_coupon_markers(loc_map[map_id].map,location_array);if(bounds.left==bounds.right)
{bounds.top-=700;bounds.bottom+=700;bounds.right+=700;bounds.left-=700;}
ol_map.custom_zoom(loc_map[map_id].map,bounds,'market');if(!loc_map[map_id].map.getCenter()){loc_map[map_id].map.zoomToMaxExtent()}},build_base_layer:function(div_id,map_id)
{if(typeof div_id=='undefined')
{div_id='displaymap';}
if(typeof map_id=='undefined')
{map_id=0;}
ol_map.market_map_setup(loc_map[map_id]);OpenLayers.ImgPath='/media/images/'
var WGS84=new OpenLayers.Projection("EPSG:4326");var options={scales:[50000000,30000000,10000000,5000000],'controls':[new OpenLayers.Control.Navigation()],'projection':new OpenLayers.Projection("EPSG:900913"),'displayProjection':WGS84,'buffer':0,'theme':null,'autoPan':true};loc_map[map_id].map=new OpenLayers.Map(div_id,options);loc_map[map_id].layers.base=new OpenLayers.Layer.Google("Google",options_dict);loc_map[map_id].map.addLayer(loc_map[map_id].layers.base);loc_map[map_id].layers.base.poweredBy='gg_watermark';var panel=new OpenLayers.Control.Panel();panel.addControls([new ol_map.buildZoomControl(options)]);loc_map[map_id].map.addControl(panel);panel.activate();},buildZoomControl:function(options)
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
{options_dict={minZoomLevel:3,maxZoomLevel:5}
ol_map.build_base_layer();ol_map.load_doc('state_geoms.txt');},build_color_list:function(color_index)
{switch(color_index)
{case 1:border_color=""
old_border_color="#63b337";color_list=[["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color],["#9cde77",border_color]]
break;default:color_list=[["#f9b7e8","#cb74b4"],["#de638f","#cb74b4"],["#ae50bf","#cb74b4"],["#d57bbd","#cb74b4"],["#c66aad","#cb74b4"],["#f9b7e8","#cb74b4"],["#e799d2","#cb74b4"],["#dd8fc8","#cb74b4"],["#d57bbd","#cb74b4"],["#c66aad","#cb74b4"]]
break;}
return color_list},build_geom_layers:function(markets,interactive,visible,mode)
{var bounds=new OpenLayers.Bounds();var this_bounds;var layer_label;var market_link;var geom_vector_data;var zoom_level='market';var style_index;var geom_data=markets.replace(/['"]/g,'');var geom_array=geom_data.split('|');var initial_layer_index;var geom_unit;var fill_opacity=0.7;if(typeof visible=="undefined"){visible=true;}
if(typeof mode=="undefined"){mode='normal';}
initial_layer_index=layer_array.length;color_type=2;geom_unit=mode;if(mode!="normal")
{color_type=1;if(mode=="whole_market")
{geom_unit='county';selection_colors=ol_map.build_color_list(2);style_array[999]=new OpenLayers.StyleMap({"default":new OpenLayers.Style({pointRadius:"${type}",fillColor:selection_colors[0][0].toString(),strokeColor:selection_colors[0][1].toString(),strokeWidth:1.3,graphicZIndex:1,fillOpacity:fill_opacity,label:"",fontColor:"#382282",fontSize:12,fontWeight:"600",labelAlign:"cm",labelXOffset:i,labelYOffset:i-2})});whole_market_layer=new OpenLayers.Layer.Vector("whole_market",{styleMap:style_array[999],LID:mode,visibility:true});}}
var color_list=ol_map.build_color_list(color_type);for(var i=0;i<geom_array.length;i++)
{geom_array[i]=geom_array[i].split(';');if(visible)
{layer_label=geom_array[i][1];}
else
{layer_label='';}
style_index=i.toString().substring(i.toString().length-1);style_array[i]=new OpenLayers.StyleMap({"default":new OpenLayers.Style({pointRadius:"${type}",fillColor:color_list[style_index][0].toString(),strokeColor:color_list[style_index][1].toString(),strokeWidth:1.3,graphicZIndex:1,fillOpacity:fill_opacity,label:layer_label,fontColor:"#382282",fontSize:12,fontWeight:"600",labelAlign:"cm",labelXOffset:i,labelYOffset:i-2})});if(geom_array[i][0]!='')
{if(geom_array[i][2]!=undefined)
{market_link=geom_array[i][2].toLowerCase();}
layer_array[initial_layer_index+i]=new OpenLayers.Layer.Vector(geom_array[i][1].replace(/ /g,'_'),{styleMap:style_array[i],mode:geom_unit,LID:market_link,visibility:visible});geom_data1=geom_array[i][0];geom_vector_data=loc_map[0].read_wkt(geom_data1);if(mode=="whole_market")
{whole_market_layer.addFeatures([geom_vector_data]);}
layer_array[initial_layer_index+i].addFeatures([geom_vector_data]);this_bounds=geom_vector_data.geometry.getBounds();bounds.extend(this_bounds);loc_map[0].map.addLayers([layer_array[initial_layer_index+i]])}}
if(interactive==true)
{var highlightCtrl=new OpenLayers.Control.SelectFeature(layer_array,{hover:true,highlightOnly:true,renderIntent:"temporary"});var selectCtrl=new OpenLayers.Control.SelectFeature(layer_array,{clickout:true,click:true,single:true,onSelect:function(e){window.location="/"+e.layer.LID.toString().replace(/\s/g,"").replace(' ','-')+'/';}});loc_map[0].map.addControl(highlightCtrl);loc_map[0].map.addControl(selectCtrl);highlightCtrl.activate();selectCtrl.activate();}
var url_path=window.location.href.toLowerCase();if(url_path.indexOf('hawaii')+loc_map[0].map.getLayersByName('Honolulu').length+loc_map[0].map.getLayersByName('Kauai').length>0)
{zoom_level='hawaii';}
else if(loc_map[0].map.getLayersByName('Anchorage').length+loc_map[0].map.getLayersByName('Aleutians_West').length>0)
{zoom_level='alaska';}
if(mode!="zip"){ol_map.custom_zoom(loc_map[0].map,bounds,zoom_level);if(!loc_map[0].map.getCenter()){loc_map[0].map.zoomToMaxExtent()}}},build_geoms_for_single_market:function(markets,interactive,visible,mode)
{ol_map.build_base_layer();ol_map.build_geom_layers(markets,interactive,visible,mode);},build_market_map:function(markets)
{options_dict={minZoomLevel:0,maxZoomLevel:10};ol_map.build_geoms_for_single_market(markets,false);},build_state_map:function(markets,interactive,visible,mode)
{options_dict={minZoomLevel:4,maxZoomLevel:7};ol_map.build_geoms_for_single_market(markets,interactive,visible,mode);},build_map_selector:function(interactive,visible,mode)
{var counties=document.getElementById('map_counties').value.replace(/['"]/g,'');options_dict={minZoomLevel:0,maxZoomLevel:10};ol_map.build_geoms_for_single_market(counties,interactive=interactive,visible=visible,mode=mode);loc_map[0].map.addLayers([whole_market_layer]);loc_map[0].map.setLayerIndex(loc_map[0].map.getLayersBy("name","whole_market")[0],1);},custom_zoom:function(map,bounds,type)
{if(typeof type=="undefined"){type="default";}
switch(type)
{case"alaska":myZoom=4;lonCenter=-152.5341796875;latCenter=62.257014469733924;break;case"hawaii":myZoom=7;lonCenter=-157.8583333;latCenter=21.3069444;break;case"market":map.zoomToExtent(bounds);return;case"continent":default:myZoom=3;lonCenter=-110.683333;latCenter=50.033333;break;}
myPoint=new OpenLayers.Geometry.Point(lonCenter,latCenter);OpenLayers.Projection.transform(myPoint,map.displayProjection,map.getProjectionObject());map.setCenter(new OpenLayers.LonLat(myPoint.x,myPoint.y),myZoom);return;},build_country_map:function()
{var bounds=new OpenLayers.Bounds();var this_bounds;var geom_data=document.getElementById('id_geom').value.replace(/['"]/g,'');var geom_array=geom_data.split('|');var layer_array=new Array();var geom_vector_data;for(var i=0;i<geom_array.length-1;i++)
{geom_array[i]=geom_array[i].split(';');style_array[i]=new OpenLayers.StyleMap({"default":new OpenLayers.Style({pointRadius:"${type}",fillColor:'#dd8fc8',strokeColor:'#cb74b4',strokeWidth:1.25,graphicZIndex:1,fillOpacity:0.2,label:geom_array[i][1],fontColor:'#fbcf79',fontSize:1,fontWeight:"000"})});layer_array[i]=new OpenLayers.Layer.Vector("Layer_"+i,{styleMap:style_array[i],LID:geom_array[i][1],'rendererOptions':{yOrdering:false,zIndexing:true}});loc_map[0].map.addLayers([layer_array[i]]);if(geom_array[i][0]!='')
{geom_data1=geom_array[i][0];geom_vector_data=loc_map[0].read_wkt(geom_data1);layer_array[i].addFeatures([geom_vector_data]);}}
var highlightCtrl=new OpenLayers.Control.SelectFeature(layer_array,{hover:true,highlightOnly:true,renderIntent:"temporary"});var selectCtrl=new OpenLayers.Control.SelectFeature(layer_array,{clickout:true,click:true,single:true,onSelect:function(e){window.location="/map/"+e.layer.LID.toString().replace(/\s/g,"").replace(' ','-')+'/';}});loc_map[0].map.addControl(highlightCtrl);loc_map[0].map.addControl(selectCtrl);highlightCtrl.activate();selectCtrl.activate();place_markers(loc_map[0].map);ol_map.custom_zoom(loc_map[0].map,bounds,'continent');},display_layer:function(geom_layer)
{this_layer=loc_map[0].map.getLayersBy("name",geom_layer)[0];this_layer.setVisibility(false);this_layer.setVisibility(true);unique_val=true;for(i=0;i<selected_geoms_array.length;i++)
{if(selected_geoms_array[i][0]==geom_layer)
{unique_val=false;break;}}
if(unique_val)
{j=selected_geoms_array.length;selected_geoms_array[j]=new Array();selected_geoms_array[j][0]=geom_layer;selected_geoms_array[j][1]=0;selected_geoms_array[j][2]=this_layer.mode;}},hide_layer:function(geom_layer)
{loc_map[0].map.getLayersBy("name",geom_layer)[0].setVisibility(false);for(i=0;i<selected_geoms_array.length;i++)
{if(selected_geoms_array[i][0]==geom_layer)
{selected_geoms_array.splice(i,1);}}
loc_map[0].map.getLayersBy("name","whole_market")[0].redraw();ol_map.redraw_checked();},redraw_checked:function()
{for(i=0;i<selected_geoms_array.length;i++)
{this_layer=loc_map[0].map.getLayersBy("name",selected_geoms_array[i][0])[0];if(this_layer.mode=='county')
{this_layer.redraw();}}},adjust_zip_zone:function(zip,miles)
{var temp_point;var line;var dist;central_zip=loc_map[0].map.getLayersBy("name",zip)[0];if(central_zip==undefined){return false;}
centroid=central_zip.features[0].geometry.getCentroid();for(var i=loc_map[0].map.layers.length-1;i>=0;i--)
{if(loc_map[0].map.layers[i].mode=='zip')
{temp_point=loc_map[0].map.layers[i].features[0].geometry.getCentroid();line=new OpenLayers.Geometry.LineString([centroid,temp_point]);if(centroid==temp_point||line.getGeodesicLength(new OpenLayers.Projection("EPSG:900913"))<=miles*1609.344)
{ol_map.display_layer(loc_map[0].map.layers[i].name);}
else if(loc_map[0].map.layers[i].visibility)
{ol_map.hide_layer(loc_map[0].map.layers[i].name);}}}
return true;},clear_zip_selections:function()
{for(n=0;n<selected_geoms_array.length;n++)
{if(loc_map[0].map.getLayersBy("name",selected_geoms_array[n][0])[0].mode=='zip')
{ol_map.hide_layer(loc_map[0].map.getLayersBy("name",selected_geoms_array[n][0])[0].name);n-=1;}}},report_selected_geoms:function()
{selected_array=new Array();for(n=0;n<selected_geoms_array.length;n++)
{selected_array[selected_array.length]=selected_geoms_array[n][0];}
return selected_array;},load_doc:function(file)
{var xmlhttp;var file_path;if(file.indexOf('state_geoms')>-1)
{file_path="/media/data/"}
else
{file_path="/media/dynamic/map-data/"}
if(window.XMLHttpRequest)
{xmlhttp=new XMLHttpRequest();}
else
{xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");}
xmlhttp.onreadystatechange=function()
{if(xmlhttp.readyState==4&&xmlhttp.status==200)
{if(file.indexOf('state_geoms')>-1)
{document.getElementById("id_geom").value=xmlhttp.responseText;ol_map.build_country_map();}
else
{marker_list=xmlhttp.responseText;ol_map.build_markets_map();}}}
xmlhttp.open("GET",file_path+file,true);xmlhttp.send();},create_market_list:function()
{ol_map.load_doc('market-geom-markers.txt');}};})();function place_coupon_markers(map,marker_array)
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
{var WGS84=new OpenLayers.Projection("EPSG:4326");marker_array=new Array();marker_style_array=new Array();marker_stylemap_array=new Array();marker_layers=new Array();marker_array=ol_map.build_location_array(eval(marker_list));marker_style_array[0]=new OpenLayers.Style({'externalGraphic':'/media/images/map_pointers/markerstar.png','graphicHeight':8,'graphicWidth':8});marker_stylemap_array[0]=new OpenLayers.StyleMap({'default':marker_style_array[0]});var markers=new OpenLayers.Layer.Vector("Markers",{'styleMap':marker_stylemap_array[0]});var features=[];for(i=0;i<marker_array.length;i++)
{myPoint=new OpenLayers.Geometry.Point(marker_array[i][0],marker_array[i][1]);OpenLayers.Projection.transform(myPoint,map.displayProjection,map.getProjectionObject());features.push(new OpenLayers.Feature.Vector(myPoint));}
markers.addFeatures(features);map.addLayer(markers);return markers.getDataExtent();}