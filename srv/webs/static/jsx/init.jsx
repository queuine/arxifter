
function pageInit() {
    const container = document.getElementById('root');
    const root = ReactDOM.createRoot(container);
    root.render(
        <BiorxivPage />
    );
}

if (
    (document.readyState == "loading")
    || (document.readyState == "uninitialized")
) {
    if (document.addEventListener) {
        document.addEventListener( "DOMContentLoaded", pageInit );
    } else {
        window.onload = pageInit;
    }
} else {
    pageInit();
}
