const form=document.querySelector('#lab-form');
const results=document.querySelector('#results');
const fields=[...form.querySelectorAll('input')];
const presets={
 normal:{scheduled_today:8,posted_today:8,actual_remaining_today:0,missed_today:0},
 auditorium:{scheduled_today:8,posted_today:5,actual_remaining_today:0,missed_today:0},
 cancelled:{scheduled_today:8,posted_today:5,actual_remaining_today:0,missed_today:0},
 late:{scheduled_today:8,posted_today:5,actual_remaining_today:3,missed_today:0},
 bunk:{scheduled_today:8,posted_today:5,actual_remaining_today:3,missed_today:3},
 custom:{}
};
function set(name,value){const el=form.elements[name];if(el&&value!==undefined)el.value=value}
function money(x){return `${Number(x).toFixed(2)}%`}
function metric(label,value){return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`}
function render(data){
 const t=data.today,c=data.checkpoint;
 results.innerHTML=`<div class="section-title">Current</div>${metric('Attendance',`${data.current.attended} / ${data.current.total}`)}${metric('Percentage',money(data.current.percentage))}<div class="section-title">Today</div>${metric('Scheduled',t.scheduled)}${metric('Posted',t.posted)}${metric('Pending',t.pending)}${metric('Actually happening',t.remaining)}${metric('Missed',t.missed)}${metric('After today',money(t.percentage))}<div class="section-title">Checkpoint</div>${metric('Future classes',c.future_classes)}${metric('Projected',money(c.percentage))}${metric('Status',`<span class="status">${c.status}</span>`)}<div class="section-title">Integrity</div>${metric('Real attendance changed',data.integrity.real_attendance_mutated?'YES':'NO')}${metric('Simulation',data.integrity.simulation_only?'YES':'NO')}`;
}
async function run(){
 const body=Object.fromEntries(new FormData(form).entries());
 const res=await fetch('/scenario-lab/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const data=await res.json();
 if(!res.ok){results.textContent=data.error||'Unable to run scenario';return}
 render(data);
}
form.addEventListener('submit',e=>{e.preventDefault();run()});
document.querySelectorAll('[data-preset]').forEach(btn=>btn.addEventListener('click',()=>{const p=presets[btn.dataset.preset];Object.entries(p).forEach(([k,v])=>set(k,v));run()}));
run();
