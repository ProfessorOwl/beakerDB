var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.SummenformelRenderer = function (props) {
    // Ensure we have a string to work with
    var val = props && props.value != null ? String(props.value) : '';

    // Split into parts, keeping digit runs (e.g. "C6H12O6" -> ["C","6","H","12","O","6"])
    var parts = val.split(/(\d+)/);

    // Build children array: non-digits as plain text, digit runs wrapped in <sub>
    var children = [];
    for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        if (p === '') continue;
        if (/^\d+$/.test(p)) {
            children.push(React.createElement('sub', { key: 's' + i }, p));
        } else {
            children.push(p);
        }
    }

    return React.createElement('div', null, children);
};