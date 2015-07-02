/*
 * SimpleModal 1.3.5 - jQuery Plugin
 * http://www.ericmmartin.com/projects/simplemodal/
 * Copyright (c) 2010 Eric Martin (http://twitter.com/EricMMartin)
 * Dual licensed under the MIT and GPL licenses
 * Revision: $Id: jquery.simplemodal.js 245 2010-03-25 20:41:15Z emartin24 $
 */
;(function($){var ie6=$.browser.msie&&parseInt($.browser.version)==6&&typeof window['XMLHttpRequest']!="object",ieQuirks=null,w=[];$.modal=function(data,options){return $.modal.impl.init(data,options);};$.modal.close=function(){$.modal.impl.close();};$.fn.modal=function(options){return $.modal.impl.init(this,options);};$.modal.defaults={appendTo:'body',focus:true,opacity:50,overlayId:'modal-overlay',overlayCss:{},containerId:'simplemodal-container',containerCss:{},dataId:'simplemodal-data',dataCss:{},minHeight:null,minWidth:null,maxHeight:null,maxWidth:null,autoResize:false,autoPosition:true,zIndex:1000,close:true,closeHTML:'<a class="sprite modalCloseImg" title="Close"></a>',closeClass:'simplemodal-close',escClose:true,overlayClose:false,position:null,persist:false,modal:true,onOpen:null,onShow:null,onClose:null};$.modal.impl={o:null,d:{},init:function(data,options){var s=this;if(s.d.data){return false;}ieQuirks=$.browser.msie&&!$.boxModel;s.o=$.extend({},$.modal.defaults,options);s.zIndex=s.o.zIndex;s.occb=false;if(typeof data=='object'){data=data instanceof jQuery?data:$(data);s.d.placeholder=false;if(data.parent().parent().size()>0){data.before($('<span></span>').attr('id','simplemodal-placeholder').css({display:'none'}));s.d.placeholder=true;s.display=data.css('display');if(!s.o.persist){s.d.orig=data.clone(true);}}}else if(typeof data=='string'||typeof data=='number'){data=$('<div></div>').html(data);}else{alert('SimpleModal Error: Unsupported data type: '+typeof data);return s;}s.create(data);data=null;s.open();if($.isFunction(s.o.onShow)){s.o.onShow.apply(s,[s.d]);}return s;},create:function(data){var s=this;w=s.getDimensions();if(s.o.modal&&ie6){s.d.iframe=$('<iframe src="javascript:false;"></iframe>').css($.extend(s.o.iframeCss,{display:'none',opacity:0,position:'fixed',height:w[0],width:w[1],zIndex:s.o.zIndex,top:0,left:0})).appendTo(s.o.appendTo);}s.d.overlay=$('<div></div>').attr('id',s.o.overlayId).addClass('modal-overlay').css($.extend(s.o.overlayCss,{display:'none',opacity:s.o.opacity/100,height:s.o.modal?w[0]:0,width:s.o.modal?w[1]:0,position:'fixed',left:0,top:0,zIndex:s.o.zIndex+1})).appendTo(s.o.appendTo);s.d.container=$('<div></div>').attr('id',s.o.containerId).addClass('simplemodal-container').css($.extend(s.o.containerCss,{display:'none',position:'fixed',zIndex:s.o.zIndex+2})).append(s.o.close&&s.o.closeHTML?$(s.o.closeHTML).addClass(s.o.closeClass):'').appendTo(s.o.appendTo);s.d.wrap=$('<div></div>').attr('tabIndex',-1).addClass('simplemodal-wrap').css({height:'100%',outline:0,width:'100%'}).appendTo(s.d.container);s.d.data=data.attr('id',data.attr('id')||s.o.dataId).addClass('simplemodal-data').css($.extend(s.o.dataCss,{display:'none'})).appendTo('body');data=null;s.setContainerDimensions();s.d.data.appendTo(s.d.wrap);if(ie6||ieQuirks){s.fixIE();}},bindEvents:function(){var s=this;$('.'+s.o.closeClass).bind('click.simplemodal',function(e){e.preventDefault();s.close();});if(s.o.modal&&s.o.close&&s.o.overlayClose){s.d.overlay.bind('click.simplemodal',function(e){e.preventDefault();s.close();});}$(document).bind('keydown.simplemodal',function(e){if(s.o.modal&&s.o.focus&&e.keyCode==9){s.watchTab(e);}else if((s.o.close&&s.o.escClose)&&e.keyCode==27){e.preventDefault();s.close();}});$(window).bind('resize.simplemodal',function(){w=s.getDimensions();s.setContainerDimensions(true);if(ie6||ieQuirks){s.fixIE();}else if(s.o.modal){s.d.iframe&&s.d.iframe.css({height:w[0],width:w[1]});s.d.overlay.css({height:w[0],width:w[1]});}});},unbindEvents:function(){$('.'+this.o.closeClass).unbind('click.simplemodal');$(document).unbind('keydown.simplemodal');$(window).unbind('resize.simplemodal');this.d.overlay.unbind('click.simplemodal');},fixIE:function(){var s=this,p=s.o.position;$.each([s.d.iframe||null,!s.o.modal?null:s.d.overlay,s.d.container],function(i,el){if(el){var bch='document.body.clientHeight',bcw='document.body.clientWidth',bsh='document.body.scrollHeight',bsl='document.body.scrollLeft',bst='document.body.scrollTop',bsw='document.body.scrollWidth',ch='document.documentElement.clientHeight',cw='document.documentElement.clientWidth',sl='document.documentElement.scrollLeft',st='document.documentElement.scrollTop',s=el[0].style;s.position='absolute';if(i<2){s.removeExpression('height');s.removeExpression('width');s.setExpression('height',''+bsh+' > '+bch+' ? '+bsh+' : '+bch+' + "px"');s.setExpression('width',''+bsw+' > '+bcw+' ? '+bsw+' : '+bcw+' + "px"');}else{var te,le;if(p&&p.constructor==Array){var top=p[0]?typeof p[0]=='number'?p[0].toString():p[0].replace(/px/,''):el.css('top').replace(/px/,'');te=top.indexOf('%')==-1?top+' + (t = '+st+' ? '+st+' : '+bst+') + "px"':parseInt(top.replace(/%/,''))+' * (('+ch+' || '+bch+') / 100) + (t = '+st+' ? '+st+' : '+bst+') + "px"';if(p[1]){var left=typeof p[1]=='number'?p[1].toString():p[1].replace(/px/,'');le=left.indexOf('%')==-1?left+' + (t = '+sl+' ? '+sl+' : '+bsl+') + "px"':parseInt(left.replace(/%/,''))+' * (('+cw+' || '+bcw+') / 100) + (t = '+sl+' ? '+sl+' : '+bsl+') + "px"';}}else{te='('+ch+' || '+bch+') / 2 - (this.offsetHeight / 2) + (t = '+st+' ? '+st+' : '+bst+') + "px"';le='('+cw+' || '+bcw+') / 2 - (this.offsetWidth / 2) + (t = '+sl+' ? '+sl+' : '+bsl+') + "px"';}s.removeExpression('top');s.removeExpression('left');s.setExpression('top',te);s.setExpression('left',le);}}});},focus:function(pos){var s=this,p=pos||'first';var input=$(':input:enabled:visible:'+p,s.d.wrap);input.length>0?input.focus():s.d.wrap.focus();},getDimensions:function(){var el=$(window);var h=$.browser.opera&&$.browser.version>'9.5'&&$.fn.jquery<='1.2.6'?document.documentElement['clientHeight']:$.browser.opera&&$.browser.version<'9.5'&&$.fn.jquery>'1.2.6'?window.innerHeight:el.height();return[h,el.width()];},getVal:function(v){return v=='auto'?0:v.indexOf('%')>0?v:parseInt(v.replace(/px/,''));},setContainerDimensions:function(resize){var s=this;if(!resize||(resize&&s.o.autoResize)){var ch=$.browser.opera?s.d.container.height():s.getVal(s.d.container.css('height')),cw=$.browser.opera?s.d.container.width():s.getVal(s.d.container.css('width')),dh=s.d.data.outerHeight(true),dw=s.d.data.outerWidth(true);var mh=s.o.maxHeight&&s.o.maxHeight<w[0]?s.o.maxHeight:w[0],mw=s.o.maxWidth&&s.o.maxWidth<w[1]?s.o.maxWidth:w[1];if(!ch){if(!dh){ch=s.o.minHeight;}else{if(dh>mh){ch=mh;}else if(dh<s.o.minHeight){ch=s.o.minHeight;}else{ch=dh;}}}else{ch=ch>mh?mh:ch;}if(!cw){if(!dw){cw=s.o.minWidth;}else{if(dw>mw){cw=mw;}else if(dw<s.o.minWidth){cw=s.o.minWidth;}else{cw=dw;}}}else{cw=cw>mw?mw:cw;}s.d.container.css({height:ch,width:cw});if(dh>ch||dw>cw){s.d.wrap.css({overflow:'auto'});}}if(s.o.autoPosition){s.setPosition();}},setPosition:function(){var s=this,top,left,hc=(w[0]/2)-(s.d.container.outerHeight(true)/2),vc=(w[1]/2)-(s.d.container.outerWidth(true)/2);if(s.o.position&&Object.prototype.toString.call(s.o.position)==="[object Array]"){top=s.o.position[0]||hc;left=s.o.position[1]||vc;}else{top=hc;left=vc;}s.d.container.css({left:left,top:top});},watchTab:function(e){var s=this;if($(e.target).parents('.simplemodal-container').length>0){s.inputs=$(':input:enabled:visible:first, :input:enabled:visible:last',s.d.data[0]);if((!e.shiftKey&&e.target==s.inputs[s.inputs.length-1])||(e.shiftKey&&e.target==s.inputs[0])||s.inputs.length==0){e.preventDefault();var pos=e.shiftKey?'last':'first';setTimeout(function(){s.focus(pos);},10);}}else{e.preventDefault();setTimeout(function(){s.focus();},10);}},open:function(){var s=this;s.d.iframe&&s.d.iframe.show();if($.isFunction(s.o.onOpen)){s.o.onOpen.apply(s,[s.d]);}else{s.d.overlay.show();s.d.container.show();s.d.data.show();}s.focus();s.bindEvents();},close:function(){var s=this;if(!s.d.data){return false;}s.unbindEvents();if($.isFunction(s.o.onClose)&&!s.occb){s.occb=true;s.o.onClose.apply(s,[s.d]);}else{if(s.d.placeholder){var ph=$('#simplemodal-placeholder');if(s.o.persist){ph.replaceWith(s.d.data.removeClass('simplemodal-data').css('display',s.display));}else{s.d.data.hide().remove();ph.replaceWith(s.d.orig);}}else{s.d.data.hide().remove();}s.d.container.hide().remove();s.d.overlay.hide().remove();s.d.iframe&&s.d.iframe.hide().remove();s.d={};}}};})(jQuery);





/*
* Disable Enter Key on form submit
*/
function disableEnterKey(e)
{
     var key;      
     if(window.event)
          key = window.event.keyCode; //IE
     else
          key = e.which; //firefox
     return (key != 13);
}




/*
 * Autotab - jQuery plugin 1.0
 * http://dev.lousyllama.com/auto-tab
 * 
 * Copyright (c) 2008 Matthew Miller
 * 
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 * 
 * Revised: 2008/05/22 01:23:25
 */

(function($) {

$.fn.autotab = function(options) {
    var defaults = {
        format: 'all',            // text, numeric, alphanumeric, all
        maxlength: 2147483647,    // Defaults to maxlength value
        uppercase: false,        // Converts a string to UPPERCASE
        lowercase: false,        // Converts a string to lowecase
        nospace: false,            // Remove spaces in the user input
        target: null,            // Where to auto tab to
        previous: null            // Backwards auto tab when all data is backspaced
    };

    $.extend(defaults, options);

    var check_element = function(name) {
        var val = null;
        var check_id = $('#' + name)[0];
        var check_name = $('input[name=' + name + ']')[0];

        if(check_id != undefined)
            val = $(check_id);
        else if(check_name != undefined)
            val = $(check_name);

        return val;
    };

    var key = function(e) {
        if(!e)
            e = window.event;

        return e.keyCode;
    };

    // Sets targets to element based on the name or ID passed
    if(typeof defaults.target == 'string')
        defaults.target = check_element(defaults.target);

    if(typeof defaults.previous == 'string')
        defaults.previous = check_element(defaults.previous);

    var maxlength = $(this).attr('maxlength');

    // Each text field has a maximum character limit of 2147483647

    // defaults.maxlength has not changed and maxlength was specified
    if(defaults.maxlength == 2147483647 && maxlength != 2147483647)
        defaults.maxlength = maxlength;
    // defaults.maxlength overrides maxlength
    else if(defaults.maxlength > 0)
        $(this).attr('maxlength', defaults.maxlength)
    // defaults.maxlength and maxlength have not been specified
    // A target cannot be used since there is no defined maxlength
    else
        defaults.target = null;

    // IE does not recognize the backspace key
    // with keypress in a blank input box
    if($.browser.msie)
    {
        this.keydown(function(e) {
            if(key(e) == 8)
            {
                var val = this.value;

                if(val.length == 0 && defaults.previous)
                    defaults.previous.focus();
            }
        });
    }

    return this.keypress(function(e) {
        if(key(e) == 8)
        {
            var val = this.value;

            if(val.length == 0 && defaults.previous)
                defaults.previous.focus();
        }
    }).keyup(function(e) {
        var val = this.value;

        switch(defaults.format)
        {
            case 'text':
                var pattern = new RegExp('[0-9]+', 'g');
                var val = val.replace(pattern, '');
                break;

            case 'alpha':
                var pattern = new RegExp('[^a-zA-Z]+', 'g');
                var val = val.replace(pattern, '');
                break;

            case 'number':
            case 'numeric':
                var pattern = new RegExp('[^0-9]+', 'g');
                var val = val.replace(pattern, '');
                break;

            case 'alphanumeric':
                var pattern = new RegExp('[^0-9a-zA-Z]+', 'g');
                var val = val.replace(pattern, '');
                break;

            case 'all':
            default:
                break;
        }

        if(defaults.nospace)
        {
            pattern = new RegExp('[ ]+', 'g');
            val = val.replace(pattern, '');
        }

        if(defaults.uppercase)
            val = val.toUpperCase();

        if(defaults.lowercase)
            val = val.toLowerCase();

        this.value = val;

        /**
         * Do not auto tab when the following keys are pressed
         * 8:    Backspace
         * 9:    Tab
         * 16:    Shift
         * 17:    Ctrl
         * 18:    Alt
         * 19:    Pause Break
         * 20:    Caps Lock
         * 27:    Esc
         * 33:    Page Up
         * 34:    Page Down
         * 35:    End
         * 36:    Home
         * 37:    Left Arrow
         * 38:    Up Arrow
         * 39:    Right Arrow
         * 40:    Down Arroww
         * 45:    Insert
         * 46:    Delete
         * 144:    Num Lock
         * 145:    Scroll Lock
         */
        var keys = [8, 9, 16, 17, 18, 19, 20, 27, 33, 34, 35, 36, 37, 38, 39, 40, 45, 46, 144, 145];
        var string = keys.toString();

        if(string.indexOf(key(e)) == -1 && val.length == defaults.maxlength && defaults.target)
            defaults.target.focus();
    });
};

})(jQuery);


// HTML Truncator for jQuery
// Free to modify and redistribute with credit.

(function($) {

  var trailing_whitespace = true;

  $.fn.truncate = function(options) {

    var opts = $.extend({}, $.fn.truncate.defaults, options);
    
    $(this).each(function() {

      var content_length = $.trim(squeeze($(this).text())).length;
      if (content_length <= opts.max_length)
        return;  // bail early if not overlong

      var actual_max_length = opts.max_length - opts.more.length - 3;  // 3 for " ()"
      var truncated_node = recursivelyTruncate(this, actual_max_length);
      var full_node = $(this).hide();

      truncated_node.insertAfter(full_node);
      
      findNodeForMore(truncated_node).append('... <a href="#show more content">'+opts.more+'</a>');
      findNodeForLess(full_node).append(' <a href="#show less content">'+opts.less+'</a>');
      
      truncated_node.find('a:last').click(function() {
        truncated_node.hide(); full_node.show(); return false;
      });
      full_node.find('a:last').click(function() {
        truncated_node.show(); full_node.hide(); return false;
      });

    });
  }

  // Note that the " (...more)" bit counts towards the max length so a max
  // length of 10 would truncate "1234567890" to "12 (...more)".
  $.fn.truncate.defaults = {
    max_length: 100,
    more: 'more',
    less: 'less'
  };

  function recursivelyTruncate(node, max_length) {
    return (node.nodeType == 3) ? truncateText(node, max_length) : truncateNode(node, max_length);
  }

  function truncateNode(node, max_length) {
    var node = $(node);
    var new_node = node.clone().empty();
    var truncatedChild;
    node.contents().each(function() {
      var remaining_length = max_length - new_node.text().length;
      if (remaining_length == 0) return;  // breaks the loop
      truncatedChild = recursivelyTruncate(this, remaining_length);
      if (truncatedChild) new_node.append(truncatedChild);
    });
    return new_node;
  }

  function truncateText(node, max_length) {
    var text = squeeze(node.data);
    if (trailing_whitespace)  // remove initial whitespace if last text
      text = text.replace(/^ /, '');  // node had trailing whitespace.
    trailing_whitespace = !!text.match(/ $/);
    var text = text.slice(0, max_length);
    // Ensure HTML entities are encoded
    // http://debuggable.com/posts/encode-html-entities-with-jquery:480f4dd6-13cc-4ce9-8071-4710cbdd56cb
    text = $('<div/>').text(text).html();
    return text;
  }

  // Collapses a sequence of whitespace into a single space.
  function squeeze(string) {
    return string.replace(/\s+/g, ' ');
  }
  
  // Finds the last, innermost block-level element
  function findNodeForMore(node) {
    var $node = $(node);
    var last_child = $node.children(":last");
    if (!last_child) return node;
    var display = last_child.css('display');
    if (!display || display=='inline') return $node;
    return findNodeForMore(last_child);
  };

  // Finds the last child if it's a p; otherwise the parent
  function findNodeForLess(node) {
    var $node = $(node);
    var last_child = $node.children(":last");
    if (last_child && last_child.is('p')) return last_child;
    return node;
  };

})(jQuery);




/* In-Field Label jQuery Plugin
 * http://fuelyourcoding.com/scripts/infield.html
 * Copyright (c) 2009 Doug Neiner
 * Dual licensed under the MIT and GPL licenses.
 * Uses the same license as jQuery, see:
 * http://docs.jquery.com/License
 * @version 0.1
 */
(function($){$.InFieldLabels=function(b,c,d){var f=this;f.$label=$(b);f.label=b;f.$field=$(c);f.field=c;f.$label.data("InFieldLabels",f);f.showing=true;f.init=function(){f.options=$.extend({},$.InFieldLabels.defaultOptions,d);if(f.$field.val()!=""){f.$label.hide();f.showing=false};f.$field.focus(function(){f.fadeOnFocus()}).blur(function(){f.checkForEmpty(true)}).bind('keydown.infieldlabel',function(e){f.hideOnChange(e)}).change(function(e){f.checkForEmpty()}).bind('onPropertyChange',function(){f.checkForEmpty()})};f.fadeOnFocus=function(){if(f.showing){f.setOpacity(f.options.fadeOpacity)}};f.setOpacity=function(a){f.$label.stop().animate({opacity:a},f.options.fadeDuration);f.showing=(a>0.0)};f.checkForEmpty=function(a){if(f.$field.val()==""){f.prepForShow();f.setOpacity(a?1.0:f.options.fadeOpacity)}else{f.setOpacity(0.0)}};f.prepForShow=function(e){if(!f.showing){f.$label.css({opacity:0.0}).show();f.$field.bind('keydown.infieldlabel',function(e){f.hideOnChange(e)})}};f.hideOnChange=function(e){if((e.keyCode==16)||(e.keyCode==9))return;if(f.showing){f.$label.hide();f.showing=false};f.$field.unbind('keydown.infieldlabel')};f.init()};$.InFieldLabels.defaultOptions={fadeOpacity:0.5,fadeDuration:300};$.fn.inFieldLabels=function(c){return this.each(function(){var a=$(this).attr('for');if(!a)return;var b=$("input#"+a+"[type='text'],"+"input#"+a+"[type='password'],"+"textarea#"+a);if(b.length==0)return;(new $.InFieldLabels(this,b[0],c))})}})(jQuery);




/**
* hoverIntent r5 // 2007.03.27 // jQuery 1.1.2+
* <http://cherne.net/brian/resources/jquery.hoverIntent.html>
* 
* @param  f  onMouseOver function || An object with configuration options
* @param  g  onMouseOut function  || Nothing (use configuration options object)
* @author    Brian Cherne <brian@cherne.net>
*/
(function($){$.fn.hoverIntent=function(f,g){var cfg={sensitivity:7,interval:100,timeout:0};cfg=$.extend(cfg,g?{over:f,out:g}:f);var cX,cY,pX,pY;var track=function(ev){cX=ev.pageX;cY=ev.pageY;};var compare=function(ev,ob){ob.hoverIntent_t=clearTimeout(ob.hoverIntent_t);if((Math.abs(pX-cX)+Math.abs(pY-cY))<cfg.sensitivity){$(ob).unbind("mousemove",track);ob.hoverIntent_s=1;return cfg.over.apply(ob,[ev]);}else{pX=cX;pY=cY;ob.hoverIntent_t=setTimeout(function(){compare(ev,ob);},cfg.interval);}};var delay=function(ev,ob){ob.hoverIntent_t=clearTimeout(ob.hoverIntent_t);ob.hoverIntent_s=0;return cfg.out.apply(ob,[ev]);};var handleHover=function(e){var p=(e.type=="mouseover"?e.fromElement:e.toElement)||e.relatedTarget;while(p&&p!=this){try{p=p.parentNode;}catch(e){p=this;}}if(p==this){return false;}var ev=jQuery.extend({},e);var ob=this;if(ob.hoverIntent_t){ob.hoverIntent_t=clearTimeout(ob.hoverIntent_t);}if(e.type=="mouseover"){pX=ev.pageX;pY=ev.pageY;$(ob).bind("mousemove",track);if(ob.hoverIntent_s!=1){ob.hoverIntent_t=setTimeout(function(){compare(ev,ob);},cfg.interval);}}else{$(ob).unbind("mousemove",track);if(ob.hoverIntent_s==1){ob.hoverIntent_t=setTimeout(function(){delay(ev,ob);},cfg.timeout);}}};return this.mouseover(handleHover).mouseout(handleHover);};})(jQuery);




// Spin.js
//fgnass.github.com/spin.js#v1.2.1
(function(a,b,c){function n(a){var b={x:a.offsetLeft,y:a.offsetTop};while(a=a.offsetParent)b.x+=a.offsetLeft,b.y+=a.offsetTop;return b}function m(a,b){for(var d in b)a[d]===c&&(a[d]=b[d]);return a}function l(a,b){for(var c in b)a.style[k(a,c)||c]=b[c];return a}function k(a,b){var e=a.style,f,g;if(e[b]!==c)return b;b=b.charAt(0).toUpperCase()+b.slice(1);for(g=0;g<d.length;g++){f=d[g]+b;if(e[f]!==c)return f}}function j(a,b,c,d){var g=["opacity",b,~~(a*100),c,d].join("-"),h=.01+c/d*100,j=Math.max(1-(1-a)/b*(100-h),a),k=f.substring(0,f.indexOf("Animation")).toLowerCase(),l=k&&"-"+k+"-"||"";e[g]||(i.insertRule("@"+l+"keyframes "+g+"{"+"0%{opacity:"+j+"}"+h+"%{opacity:"+a+"}"+(h+.01)+"%{opacity:1}"+(h+b)%100+"%{opacity:"+a+"}"+"100%{opacity:"+j+"}"+"}",0),e[g]=1);return g}function h(a,b,c){c&&!c.parentNode&&h(a,c),a.insertBefore(b,c||null);return a}function g(a,c){var d=b.createElement(a||"div"),e;for(e in c)d[e]=c[e];return d}var d=["webkit","Moz","ms","O"],e={},f;h(b.getElementsByTagName("head")[0],g("style"));var i=b.styleSheets[b.styleSheets.length-1],o=function q(a){if(!this.spin)return new q(a);this.opts=m(a||{},{lines:12,length:7,width:5,radius:10,color:"#000",speed:1,trail:100,opacity:.25,fps:20})},p=o.prototype={spin:function(a){this.stop();var b=this,c=b.el=l(g(),{position:"relative"}),d,e;a&&(e=n(h(a,c,a.firstChild)),d=n(c),l(c,{left:(a.offsetWidth>>1)-d.x+e.x+"px",top:(a.offsetHeight>>1)-d.y+e.y+"px"})),c.setAttribute("aria-role","progressbar"),b.lines(c,b.opts);if(!f){var i=b.opts,j=0,k=i.fps,m=k/i.speed,o=(1-i.opacity)/(m*i.trail/100),p=m/i.lines;(function q(){j++;for(var a=i.lines;a;a--){var d=Math.max(1-(j+a*p)%m*o,i.opacity);b.opacity(c,i.lines-a,d,i)}b.timeout=b.el&&setTimeout(q,~~(1e3/k))})()}return b},stop:function(){var a=this.el;a&&(clearTimeout(this.timeout),a.parentNode&&a.parentNode.removeChild(a),this.el=c);return this}};p.lines=function(a,b){function e(a,d){return l(g(),{position:"absolute",width:b.length+b.width+"px",height:b.width+"px",background:a,boxShadow:d,transformOrigin:"left",transform:"rotate("+~~(360/b.lines*c)+"deg) translate("+b.radius+"px"+",0)",borderRadius:(b.width>>1)+"px"})}var c=0,d;for(;c<b.lines;c++)d=l(g(),{position:"absolute",top:1+~(b.width/2)+"px",transform:"translate3d(0,0,0)",opacity:b.opacity,animation:f&&j(b.opacity,b.trail,c,b.lines)+" "+1/b.speed+"s linear infinite"}),b.shadow&&h(d,l(e("#000","0 0 4px #000"),{top:"2px"})),h(a,h(d,e(b.color,"0 0 1px rgba(0,0,0,.1)")));return a},p.opacity=function(a,b,c){b<a.childNodes.length&&(a.childNodes[b].style.opacity=c)},function(){var a=l(g("group"),{behavior:"url(#default#VML)"}),b;if(!k(a,"transform")&&a.adj){for(b=4;b--;)i.addRule(["group","roundrect","fill","stroke"][b],"behavior:url(#default#VML)");p.lines=function(a,b){function k(a,d,i){h(f,h(l(e(),{rotation:360/b.lines*a+"deg",left:~~d}),h(l(g("roundrect",{arcsize:1}),{width:c,height:b.width,left:b.radius,top:-b.width>>1,filter:i}),g("fill",{color:b.color,opacity:b.opacity}),g("stroke",{opacity:0}))))}function e(){return l(g("group",{coordsize:d+" "+d,coordorigin:-c+" "+ -c}),{width:d,height:d})}var c=b.length+b.width,d=2*c,f=e(),i=~(b.length+b.radius+b.width)+"px",j;if(b.shadow)for(j=1;j<=b.lines;j++)k(j,-2,"progid:DXImageTransform.Microsoft.Blur(pixelradius=2,makeshadow=1,shadowopacity=.3)");for(j=1;j<=b.lines;j++)k(j);return h(l(a,{margin:i+" 0 0 "+i,zoom:1}),f)},p.opacity=function(a,b,c,d){var e=a.firstChild;d=d.shadow&&d.lines||0,e&&b+d<e.childNodes.length&&(e=e.childNodes[b+d],e=e&&e.firstChild,e=e&&e.firstChild,e&&(e.opacity=c))}}else f=k(a,"animation")}(),a.Spinner=o})(window,document)
