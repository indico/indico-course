"use strict";!function(){var a,s,t,o;$.event.special.resize||$.fn.off.elementResizeOriginalOff||(a={index:0,check:function(e){e[$.expando]||(e[$.expando]=++a.index)},make:function(e,t){return a.check(e),t.guid+"-"+e[$.expando]}},t={lastStartEvent:0,timeoutHandle:null,intervalDuration:100,hasRaf:!(s={registered:[],shouldReProcess:!0,register:function(e,t){var n=$(e);s.registered.push({id:a.make(e,t),$element:n,_measurement:o.get(n).uniqueMeasurementId,_hasTriggered:!1}),s.shouldReProcess=!0},unregister:function(e,t){for(var n=s.registered,i=a.make(e,t),r=n.length-1;-1<r;r--){n[r].id==i&&(n.splice(r,1),s.shouldReProcess=!0)}},process:function(){var e,t=s.registered;for(s.shouldReProcess=!0;s.shouldReProcess;){if(s.shouldReProcess=!1,0==(e=t.length))return;for(var n=0;n<e;n++){var i=t[n],r=o.get(i.$element);if(void 0!==i._measurement&&i._hasTriggered)if(!(i._measurement!=r.uniqueMeasurementId))continue;if(i._measurement=r.uniqueMeasurementId,i._hasTriggered=!0,s.trigger(i),s.shouldReProcess)break}}},trigger:function(e){e.$element.trigger("resize")}}),start:function(){t.lastStartEvent=(new Date).getTime(),t.repeat()},force:function(){t.lastStartEvent=(new Date).getTime(),t.main(!0),t.repeat()},repeat:function(){t.stop(),t.hasRaf?t.timeoutHandle=requestAnimationFrame(t.main):t.timeoutHandle=setTimeout(t.main,t.intervalDuration)},hasExpired:function(){if(!((new Date).getTime()-t.lastStartEvent<1500))return t.stop(),!0},lastMain:(new Date).getTime(),isThrottled:function(){return!((new Date).getTime()-t.lastMain>t.intervalDuration)},main:function(e){!0!==e&&t.isThrottled()?t.repeat():(t.lastMain=(new Date).getTime(),!0!==e&&t.hasExpired()?t.stop():(0==s.registered.length?(t.stop(),t.intervalDuration=200):(t.stop(),t.intervalDuration=100),t.repeat(),s.process()))},stop:function(){null!==t.timeoutHandle&&((t.hasRaf?cancelAnimationFrame:clearTimeout)(t.timeoutHandle),t.timeoutHandle=null)}},$.extend($.event.special,{resize:{noBubble:!0,add:function(e){this!==window&&s.register(this,e)},remove:function(e){this!==window&&s.unregister(this,e)}}}),o={featureDetect:function(){t.hasRaf=window.requestAnimationFrame&&window.cancelAnimationFrame},get:function(e){var t=e[0];return{uniqueMeasurementId:t.clientHeight+","+t.clientWidth}}},$(window).on({"touchmove scroll mousedown keydown":t.start,resize:t.force}),$(o.featureDetect))}();