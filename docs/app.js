const DATA_URL="./data/dashboard.json";
const el=id=>document.getElementById(id);
const fmt=n=>new Intl.NumberFormat().format(n??0);
const set=(id,value)=>{el(id).textContent=value;};
function renderSpecies(items){
 const host=el("species-list"),q=el("species-search").value.trim().toLowerCase();
 const found=items.filter(x=>(x.label||"").toLowerCase().includes(q)||(x.scientific_name||"").toLowerCase().includes(q));
 const max=Math.max(1,...items.map(x=>x.detections));host.innerHTML="";
 if(!found.length){host.textContent="No candidate labels match this search.";return;}
 found.slice(0,30).forEach(x=>{
  const row=document.createElement("div");row.className="species-item";
  const name=document.createElement("strong");name.textContent=x.label;
  const count=document.createElement("span");count.textContent=fmt(x.detections);
  const sci=document.createElement("small");sci.textContent=x.scientific_name||"Scientific name not supplied";
  const track=document.createElement("div");track.className="track";
  const fill=document.createElement("span");fill.style.width=(100*x.detections/max)+"%";
  track.append(fill);row.append(name,count,sci,track);host.append(row);
 });
}
function renderHourly(items){
 const host=el("hourly-chart"),max=Math.max(1,...items.map(x=>x.detections));host.innerHTML="";
 items.forEach(x=>{
  const col=document.createElement("div");col.className="hour";
  const count=document.createElement("b");count.textContent=x.detections?fmt(x.detections):"";
  const bar=document.createElement("i");bar.style.height=Math.max(2,125*x.detections/max)+"px";
  bar.title=String(x.hour).padStart(2,"0")+":00 — "+x.detections+" detections";
  const label=document.createElement("small");label.textContent=String(x.hour).padStart(2,"0");
  col.append(count,bar,label);host.append(col);
 });
}
function renderDaily(items){
 const host=el("daily-chart"),recent=items.slice(-14),max=Math.max(1,...recent.map(x=>x.detections));host.innerHTML="";
 if(!recent.length){host.textContent="No dated detections yet.";return;}
 recent.forEach(x=>{
  const row=document.createElement("div");row.className="daily-row";
  const date=document.createElement("span");date.textContent=x.date;
  const track=document.createElement("div");track.className="track";
  const fill=document.createElement("span");fill.style.width=(100*x.detections/max)+"%";track.append(fill);
  const count=document.createElement("em");count.textContent=fmt(x.detections);
  row.append(date,track,count);host.append(row);
 });
}
async function load(){
 try{
  const response=await fetch(DATA_URL,{cache:"no-store"});if(!response.ok)throw new Error("HTTP "+response.status);
  const data=await response.json(),s=data.summary||{};
  set("recordings",fmt(s.recordings));set("detections",fmt(s.detections));set("labels",fmt(s.candidate_labels));set("filtered-out",fmt(s.filtered_out_detections));
  set("confidence",s.average_confidence==null?"—":(100*s.average_confidence).toFixed(1)+"%");
  set("duration",(Number(s.total_recording_hours||0)).toFixed(2)+" h");
  set("shannon",s.shannon_diversity==null?"—":Number(s.shannon_diversity).toFixed(3));
  set("simpson",s.simpson_diversity==null?"—":Number(s.simpson_diversity).toFixed(3));
  set("updated","Data export: "+(data.generated_at||"date unavailable"));set("footer-date",new Date().getFullYear());
  renderSpecies(data.species||[]);renderHourly(data.hourly||[]);renderDaily(data.daily||[]);
  const notes=el("notes");notes.innerHTML="";
  (data.interpretation_notes||[]).forEach(note=>{const li=document.createElement("li");li.textContent=note;notes.append(li);});
  el("species-search").addEventListener("input",()=>renderSpecies(data.species||[]));
 }catch(err){
  set("updated","Dashboard data unavailable: "+err.message);
  el("species-list").textContent="Run publish_static.py locally and publish docs/data/dashboard.json.";
  el("hourly-chart").textContent="No data loaded.";el("daily-chart").textContent="No data loaded.";
 }
}
load();