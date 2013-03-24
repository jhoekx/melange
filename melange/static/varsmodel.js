"use strict";

( function (scope) {

var VariableValueModel = function (key, value, origin) {
    var self = this;
    self.origin = origin;

    self.key = ko.observable(key);

    if (value.charAt || value.toPrecision) {
        self.type = ko.observable("text");
        self.value = ko.observable(value);
    } else if (value.map) {
        self.type = ko.observable("list");
        self.value = ko.observableArray(value.map(function(el) {
            return {value: ko.observable(el)};
        }));
    } else {
        self.type = ko.observable("map");
        self.value = ko.observableArray();
        for (var k in value) {
            self.value.push({k: ko.observable(k), v:ko.observable(value[k])});
        }
    }

    self.addListValue = function () {
        self.value.push({value: ko.observable("")});
    };

    self.removeListValue = function(val) {
        self.value.remove(val);
    };

    self.addMapValue = function () {
        self.value.push({k:ko.observable(""), v:ko.observable("")});
    };

    self.removeMapValue = function (val) {
        self.value.remove(val);
    };
};

var VariableModel = function (json_data, savefn) {
    var self = this;
    self.savefn = savefn;

    self.types = ['text', 'list', 'map'];

    var keys = [];
    var variables = [];
    if (json_data.map) {
        // list
        variables = json_data.map(function (property) {
            if (property.tag) {
                return new VariableValueModel(property.key, property.value, 
                                              {tag: property.tag, href: property.href});
            } else {
                return new VariableValueModel(property.key, property.value);
            }
        } );
    } else {
        // dict
        for (var key in json_data) {
            keys.push(key);
        }
        keys.sort();
        keys.forEach( function (key) {
            variables.push(new VariableValueModel(key, json_data[key]));
        } );
    }
    self.variables = ko.observableArray(variables);

    self.addVar = function () {
        var type = document.getElementById("variable-type").value;
        var value;
        if (type==="text") {
            value = "";
        } else if (type==="list") {
            value = [""];
        } else if (type==="map") {
            value = {'':''};
        }
        self.variables.push(new VariableValueModel("", value));
    };

    self.removeVar = function (item) {
        self.variables.remove(item);
    };

    self.save = function () {
        var vars = {};
        var items = ko.toJS(self.variables);
        items.forEach( function (item) {
            if (item.origin) {
                return;
            }
            var k = item['key'];
            var v = item['value'];
            if ( k && v ) {
                if (item['type']==="text") {
                    vars[k] = v;
                } else if (item["type"]==="list") {
                    vars[k] = v.map( function (el) {
                        return el.value;
                    } );
                } else if (item["type"]==="map") {
                    vars[k] = {};
                    v.forEach( function(el) {
                        vars[k][el.k] = el.v;
                    } );
                }
            }
        } );
        self.savefn(vars);
    };
};

addEventListener("load", function () {
    var item;
    var item_uri = document.getElementById("var-editor").getAttribute("data-model");

    var savefn = function (vars) {
        var xhr = new XMLHttpRequest();
        xhr.open("PUT", item_uri);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status!==200) {
                alert("Failed to save: "+xhr.status+"\r\n"+xhr.responseText);
            }
        };
        xhr.setRequestHeader("Content-Type", "application/json");
        item.vars = vars;
        xhr.send(JSON.stringify(item));
    };

    var xhr = new XMLHttpRequest();
    xhr.open("GET", item_uri);
    xhr.onreadystatechange = function () {
        if (xhr.readyState===4 && xhr.status===200 || xhr.status===304 ) {
            item = JSON.parse(xhr.responseText);
            ko.applyBindings(new VariableModel(item.vars, savefn), document.getElementById("var-editor"));
        }
    }
    xhr.send("");
}, false);

})(window);
