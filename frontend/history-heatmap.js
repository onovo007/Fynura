/* A second view of the same reported history, not a vaccination-effect estimate. */
window.renderHistoryHeatmap=function(data){
  if(data.frequency==='outbreak'||!data.points.some(p=>p.value!=null))return '';
  const monthly=data.frequency==='monthly',periods=new Map(data.points.map(p=>[p.period,p]));
  const years=Array.from({length:data.end-data.start+1},(_,i)=>data.start+i);
  const max=Math.max(1,...data.points.filter(p=>p.value!=null).map(p=>p.value));
  const bins=[0,.01,.1,.4,.7,1],colors=['#f0f7ee','#c6dfc8','#8dc4ac','#459b88','#136c63','#06443f'];
  const color=value=>value==null?'#e4e5e6':colors[bins.reduce((index,b,i)=>value/max>=b?i:index,0)];
  const width=900,cell=monthly?58:72,columns=monthly?12:10;
  const groups=monthly?years:Array.from(new Set(years.map(y=>Math.floor(y/10)*10)));
  const height=90+groups.length*34;
  let svg='<svg viewBox="0 0 '+width+' '+height+'" style="min-width:700px;width:100%" role="group" aria-label="'+safe(data.geography)+' historical reported-case heatmap">';
  const headings=monthly?['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']:Array.from({length:10},(_,i)=>'+'+i);
  svg+=headings.map((m,i)=>'<text x="'+(100+i*cell)+'" y="25" font-size="12">'+m+'</text>').join('');
  groups.forEach((group,row)=>{
    svg+='<text x="15" y="'+(57+row*34)+'" font-size="13">'+group+(monthly?'':'s')+'</text>';
    for(let col=0;col<columns;col++){
      const year=monthly?group:group+col;if(year<data.start||year>data.end)continue;
      const period=monthly?year+'-'+String(col+1).padStart(2,'0'):String(year),p=periods.get(period),v=p?.value;
      const label=data.geography+' · '+period+' · '+(v==null?'No reported value':fmt(v)+' '+data.unit)+' · '+data.source;
      svg+='<g tabindex="0" role="img" aria-label="'+safe(label)+'"><title>'+safe(label)+'</title><rect x="'+(96+col*cell)+'" y="'+(36+row*34)+'" width="'+(cell-5)+'" height="28" rx="3" fill="'+color(v)+'"/>'+(v==null?'<text x="'+(110+col*cell)+'" y="'+(55+row*34)+'" fill="#555" font-size="12">N/A</text>':'')+'</g>';
    }
  });
  svg+='</svg>';
  return '<article class="history-calendar"><h3>Reported-case intensity through time</h3><p>'+safe(data.geography)+' · '+safe(data.frequency)+' reports. Darker cells indicate higher reported counts within this selected series.</p><div style="overflow:auto">'+svg+'</div><div class="heatmap-key">'+bins.map((b,i)=>'<span><i style="display:inline-block;width:16px;height:16px;background:'+colors[i]+'"></i> '+(i===0?'0':fmt(Math.ceil(max*b)))+(i===bins.length-1?' (maximum)':'')+'</span>').join(' · ')+' · Grey / N/A: no report</div><p>Hover or focus a cell for period, count and source. The provenance table below contains the same observations. Source: <a target="_blank" rel="noopener" href="'+safe(data.source_url)+'">'+safe(data.source)+'</a>. Retrieved '+safe(data.retrieved_at)+'.</p></article>';
};
