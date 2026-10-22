/* A compact seasonal summary of reported history; never a forecast or imputed series. */
window.renderHistoryHeatmap=function(data){
  if(data.frequency!=='monthly')return '';
  const reported=data.points.filter(p=>p.value!=null&&/^\d{4}-\d{2}$/.test(p.period));
  const years=new Set(reported.map(p=>p.period.slice(0,4)));
  if(reported.length<24||years.size<2)return '';
  const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const groups=Array.from({length:12},()=>[]);
  reported.forEach(p=>groups[Number(p.period.slice(5,7))-1].push(Number(p.value)));
  const median=values=>{if(!values.length)return null;const sorted=[...values].sort((a,b)=>a-b),middle=Math.floor(sorted.length/2);return sorted.length%2?sorted[middle]:(sorted[middle-1]+sorted[middle])/2};
  const summaries=groups.map(values=>({value:median(values),count:values.length}));
  const max=Math.max(1,...summaries.map(item=>item.value??0));
  const bars=summaries.map((item,index)=>{
    const value=item.value,height=value==null?0:Math.max(3,Math.round(value/max*124));
    const detail=value==null?`${data.geography} · ${monthNames[index]} · no reported periods`:`${data.geography} · ${monthNames[index]} · median ${fmt(value)} ${data.unit} from ${item.count} reported period${item.count===1?'':'s'}`;
    return '<div class="seasonal-month" role="img" tabindex="0" aria-label="'+safe(detail)+'"><div class="seasonal-bar-wrap"><span class="seasonal-bar" style="height:'+height+'px" title="'+safe(detail)+'"></span></div><b>'+monthNames[index]+'</b><small>'+(value==null?'No data':'n='+item.count)+'</small></div>';
  }).join('');
  return '<article class="seasonal-profile"><h3>Typical reporting pattern by month</h3><p>'+safe(data.geography)+' · Median source-reported cases for each calendar month across '+years.size+' years.</p><div class="seasonal-chart" role="group" aria-label="'+safe(data.geography)+' seasonal reporting profile">'+bars+'</div><p class="seasonal-note">Missing reporting periods are excluded, not treated as zero. This descriptive summary can reveal recurring reporting patterns; it does not estimate seasonality or forecast an outbreak. Source: <a target="_blank" rel="noopener" href="'+safe(data.source_url)+'">'+safe(data.source)+'</a>. Retrieved '+safe(data.retrieved_at)+'.</p></article>';
};
