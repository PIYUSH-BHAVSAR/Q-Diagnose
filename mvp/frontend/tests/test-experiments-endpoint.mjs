// Test experiments endpoint directly
const BASE = 'https://dung-ununited-seriately.ngrok-free.dev/api';

console.log('Testing GET /api/experiments...\n');

try {
  const res = await fetch(`${BASE}/experiments`, {
    method: 'GET',
    headers: { 
      'ngrok-skip-browser-warning': 'true',
      'Content-Type': 'application/json'
    }
  });
  
  console.log(`Status: ${res.status} ${res.statusText}`);
  
  const data = await res.json();
  console.log('Response:', JSON.stringify(data, null, 2));
  
  if (res.status === 200) {
    console.log('\n✅ SUCCESS! GET /api/experiments is now working!');
    console.log(`Found ${data.experiments?.length || 0} experiments`);
  } else {
    console.log('\n❌ Still getting error. Backend may need restart or ngrok refresh.');
  }
} catch (e) {
  console.log('❌ Error:', e.message);
}
