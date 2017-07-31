(function(d){typeof module==="object"&&module.exports?module.exports=d:d(Highcharts)})(function(d){function A(b,a,f){var c;!a.rgba.length||!b.rgba.length?b=a.input||"none":(b=b.rgba,a=a.rgba,c=a[3]!==1||b[3]!==1,b=(c?"rgba(":"rgb(")+Math.round(a[0]+(b[0]-a[0])*(1-f))+","+Math.round(a[1]+(b[1]-a[1])*(1-f))+","+Math.round(a[2]+(b[2]-a[2])*(1-f))+(c?","+(a[3]+(b[3]-a[3])*(1-f)):"")+")");return b}var u=function(){},q=d.getOptions(),i=d.each,o=d.extend,B=d.format,C=d.merge,v=d.pick,r=d.wrap,l=d.Chart,
p=d.seriesTypes,w=p.pie,m=p.column,x=d.Tick,s=d.fireEvent,y=d.inArray,z=1;i(["fill","stroke"],function(b){d.Fx.prototype[b+"Setter"]=function(){this.elem.attr(b,A(d.Color(this.start),d.Color(this.end),this.pos))}});o(q.lang,{drillUpText:"\u25c1 Back to {series.name}"});q.drilldown={activeAxisLabelStyle:{cursor:"pointer",color:"#0d233a",fontWeight:"bold",textDecoration:"underline"},activeDataLabelStyle:{cursor:"pointer",fontWeight:"bold",textDecoration:"underline"},animation:{duration:500},drillUpButton:{position:{align:"right",
x:-10,y:10}}};d.SVGRenderer.prototype.Element.prototype.fadeIn=function(b){this.attr({opacity:0.1,visibility:"inherit"}).animate({opacity:v(this.newOpacity,1)},b||{duration:250})};l.prototype.addSeriesAsDrilldown=function(b,a){this.addSingleSeriesAsDrilldown(b,a);this.applyDrilldown()};l.prototype.addSingleSeriesAsDrilldown=function(b,a){var f=b.series,c=f.xAxis,g=f.yAxis,e;e=b.color||f.color;var h,d=[],j=[],k,n;if(!this.drilldownLevels)this.drilldownLevels=[];k=f.options._levelNumber||0;(n=this.drilldownLevels[this.drilldownLevels.length-
1])&&n.levelNumber!==k&&(n=void 0);if(!a.color)a.color=e;a._ddSeriesId=z++;h=y(b,f.points);i(f.chart.series,function(a){if(a.xAxis===c&&!a.isDrilling)a.options._ddSeriesId=a.options._ddSeriesId||z++,a.options._colorIndex=a.userOptions._colorIndex,a.options._levelNumber=a.options._levelNumber||k,n?(d=n.levelSeries,j=n.levelSeriesOptions):(d.push(a),j.push(a.options))});e={levelNumber:k,seriesOptions:f.options,levelSeriesOptions:j,levelSeries:d,shapeArgs:b.shapeArgs,bBox:b.graphic?b.graphic.getBBox():
{},color:b.isNull?(new Highcharts.Color(e)).setOpacity(0).get():e,lowerSeriesOptions:a,pointOptions:f.options.data[h],pointIndex:h,oldExtremes:{xMin:c&&c.userMin,xMax:c&&c.userMax,yMin:g&&g.userMin,yMax:g&&g.userMax}};this.drilldownLevels.push(e);e=e.lowerSeries=this.addSeries(a,!1);e.options._levelNumber=k+1;if(c)c.oldPos=c.pos,c.userMin=c.userMax=null,g.userMin=g.userMax=null;if(f.type===e.type)e.animate=e.animateDrilldown||u,e.options.animation=!0};l.prototype.applyDrilldown=function(){var b=this.drilldownLevels,
a;if(b&&b.length>0)a=b[b.length-1].levelNumber,i(this.drilldownLevels,function(b){b.levelNumber===a&&i(b.levelSeries,function(b){b.options&&b.options._levelNumber===a&&b.remove(!1)})});this.redraw();this.showDrillUpButton()};l.prototype.getDrilldownBackText=function(){var b=this.drilldownLevels;if(b&&b.length>0)return b=b[b.length-1],b.series=b.seriesOptions,B(this.options.lang.drillUpText,b)};l.prototype.showDrillUpButton=function(){var b=this,a=this.getDrilldownBackText(),f=b.options.drilldown.drillUpButton,
c,g;this.drillUpButton?this.drillUpButton.attr({text:a}).align():(g=(c=f.theme)&&c.states,this.drillUpButton=this.renderer.button(a,null,null,function(){b.drillUp()},c,g&&g.hover,g&&g.select).attr({align:f.position.align,zIndex:9}).add().align(f.position,!1,f.relativeTo||"plotBox"))};l.prototype.drillUp=function(){for(var b=this,a=b.drilldownLevels,f=a[a.length-1].levelNumber,c=a.length,g=b.series,e,h,d,j,k=function(a){var c;i(g,function(b){b.options._ddSeriesId===a._ddSeriesId&&(c=b)});c=c||b.addSeries(a,
!1);if(c.type===d.type&&c.animateDrillupTo)c.animate=c.animateDrillupTo;a===h.seriesOptions&&(j=c)};c--;)if(h=a[c],h.levelNumber===f){a.pop();d=h.lowerSeries;if(!d.chart)for(e=g.length;e--;)if(g[e].options.id===h.lowerSeriesOptions.id&&g[e].options._levelNumber===f+1){d=g[e];break}d.xData=[];i(h.levelSeriesOptions,k);s(b,"drillup",{seriesOptions:h.seriesOptions});if(j.type===d.type)j.drilldownLevel=h,j.options.animation=b.options.drilldown.animation,d.animateDrillupFrom&&d.chart&&d.animateDrillupFrom(h);
j.options._levelNumber=f;d.remove(!1);if(j.xAxis)e=h.oldExtremes,j.xAxis.setExtremes(e.xMin,e.xMax,!1),j.yAxis.setExtremes(e.yMin,e.yMax,!1)}s(b,"drillupall");this.redraw();this.drilldownLevels.length===0?this.drillUpButton=this.drillUpButton.destroy():this.drillUpButton.attr({text:this.getDrilldownBackText()}).align();this.ddDupes.length=[]};m.prototype.supportsDrilldown=!0;m.prototype.animateDrillupTo=function(b){if(!b){var a=this,f=a.drilldownLevel;i(this.points,function(a){a.graphic&&a.graphic.hide();
a.dataLabel&&a.dataLabel.hide();a.connector&&a.connector.hide()});setTimeout(function(){a.points&&i(a.points,function(a,b){var e=b===(f&&f.pointIndex)?"show":"fadeIn",d=e==="show"?!0:void 0;if(a.graphic)a.graphic[e](d);if(a.dataLabel)a.dataLabel[e](d);if(a.connector)a.connector[e](d)})},Math.max(this.chart.options.drilldown.animation.duration-50,0));this.animate=u}};m.prototype.animateDrilldown=function(b){var a=this,f=this.chart.drilldownLevels,c,g=this.chart.options.drilldown.animation,e=this.xAxis;
if(!b)i(f,function(b){if(a.options._ddSeriesId===b.lowerSeriesOptions._ddSeriesId)c=b.shapeArgs,c.fill=b.color}),c.x+=v(e.oldPos,e.pos)-e.pos,i(this.points,function(b){b.graphic&&b.graphic.attr(c).animate(o(b.shapeArgs,{fill:b.color||a.color}),g);b.dataLabel&&b.dataLabel.fadeIn(g)}),this.animate=null};m.prototype.animateDrillupFrom=function(b){var a=this.chart.options.drilldown.animation,f=this.group,c=this;i(c.trackerGroups,function(a){if(c[a])c[a].on("mouseover")});delete this.group;i(this.points,
function(c){var e=c.graphic,h=function(){e.destroy();f&&(f=f.destroy())};e&&(delete c.graphic,a?e.animate(o(b.shapeArgs,{fill:b.color}),d.merge(a,{complete:h})):(e.attr(b.shapeArgs),h()))})};w&&o(w.prototype,{supportsDrilldown:!0,animateDrillupTo:m.prototype.animateDrillupTo,animateDrillupFrom:m.prototype.animateDrillupFrom,animateDrilldown:function(b){var a=this.chart.drilldownLevels[this.chart.drilldownLevels.length-1],f=this.chart.options.drilldown.animation,c=a.shapeArgs,g=c.start,e=(c.end-g)/
this.points.length;if(!b)i(this.points,function(b,i){if(b.graphic)b.graphic.attr(d.merge(c,{start:g+i*e,end:g+(i+1)*e,fill:a.color}))[f?"animate":"attr"](o(b.shapeArgs,{fill:b.color}),f)}),this.animate=null}});d.Point.prototype.doDrilldown=function(b,a,f){var c=this.series.chart,d=c.options.drilldown,e=(d.series||[]).length,h;if(!c.ddDupes)c.ddDupes=[];for(;e--&&!h;)d.series[e].id===this.drilldown&&y(this.drilldown,c.ddDupes)===-1&&(h=d.series[e],c.ddDupes.push(this.drilldown));s(c,"drilldown",{point:this,
seriesOptions:h,category:a,originalEvent:f,points:a!==void 0&&this.series.xAxis.getDDPoints(a).slice(0)},function(a){var c=a.point.series&&a.point.series.chart,e=a.seriesOptions;c&&e&&(b?c.addSingleSeriesAsDrilldown(a.point,e):c.addSeriesAsDrilldown(a.point,e))})};d.Axis.prototype.drilldownCategory=function(b,a){var f,c,d=this.getDDPoints(b);for(f in d)(c=d[f])&&c.series&&c.series.visible&&c.doDrilldown&&c.doDrilldown(!0,b,a);this.chart.applyDrilldown()};d.Axis.prototype.getDDPoints=function(b){var a=
[];i(this.series,function(f){var c,d=f.xData,e=f.points;for(c=0;c<d.length;c++)if(d[c]===b&&f.options.data[c].drilldown){a.push(e?e[c]:!0);break}});return a};x.prototype.drillable=function(){var b=this.pos,a=this.label,f=this.axis,c=f.coll==="xAxis"&&f.getDDPoints,g=c&&f.getDDPoints(b);if(c)if(a&&g.length){if(!a.basicStyles)a.basicStyles=d.merge(a.styles);a.addClass("highcharts-drilldown-axis-label").css(f.chart.options.drilldown.activeAxisLabelStyle).on("click",function(a){f.drilldownCategory(b,
a)})}else if(a&&a.basicStyles)a.styles={},a.css(a.basicStyles),a.on("click",null)};r(x.prototype,"addLabel",function(b){b.call(this);this.drillable()});r(d.Point.prototype,"init",function(b,a,f,c){var g=b.call(this,a,f,c),b=(b=a.xAxis)&&b.ticks[c];g.drilldown&&d.addEvent(g,"click",function(b){a.xAxis&&a.chart.options.drilldown.allowPointDrilldown===!1?a.xAxis.drilldownCategory(c,b):g.doDrilldown(void 0,void 0,b)});b&&b.drillable();return g});r(d.Series.prototype,"drawDataLabels",function(b){var a=
this,d=a.chart.options.drilldown.activeDataLabelStyle,c=a.chart.renderer;b.call(a);i(a.points,function(b){var e={};if(b.drilldown&&b.dataLabel){if(d.color==="contrast")e.color=c.getContrast(b.color||a.color);b.dataLabel.attr({"class":"highcharts-drilldown-data-label"}).css(C(d,e))}})});var t,q=function(b){b.call(this);i(this.points,function(a){a.drilldown&&a.graphic&&a.graphic.attr({"class":"highcharts-drilldown-point"}).css({cursor:"pointer"})})};for(t in p)p[t].prototype.supportsDrilldown&&r(p[t].prototype,
"drawTracker",q)});
