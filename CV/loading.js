document.addEventListener('DOMContentLoaded', () => {
    console.log('loading.js');
    console.log(`body has ${document.body.childElementCount} children`);
    
    let isLight = true;
    setInterval(() => {
        document.body.style.backgroundColor = isLight ? '#ffffff' : '#ce3434';
        isLight = !isLight;
    }, 1000);
});


