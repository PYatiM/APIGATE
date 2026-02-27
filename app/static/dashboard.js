async function fetchStats() {
    const res = await fetch('/metrics');
    const data = await res.json();
    console.log(data);
}

setInterval(fetchStats, 5000);