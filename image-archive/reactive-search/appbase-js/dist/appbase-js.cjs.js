'use strict';

function _interopDefault (ex) { return (ex && (typeof ex === 'object') && 'default' in ex) ? ex['default'] : ex; }

var URL = _interopDefault(require('url-parser-lite'));
var querystring = _interopDefault(require('querystring'));
var fetch = _interopDefault(require('cross-fetch'));
var stringify = _interopDefault(require('json-stable-stringify'));

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) {
  return typeof obj;
} : function (obj) {
  return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
};

function contains(string, substring) {
  return string.indexOf(substring) !== -1;
}
function isAppbase(url) {
  return contains(url, 'scalr.api.appbase.io');
}
function btoa() {
  var input = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '';

  var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
  var str = input;
  var output = '';

  // eslint-disable-next-line
  for (var block = 0, charCode, i = 0, map = chars; str.charAt(i | 0) || (map = '=', i % 1); // eslint-disable-line no-bitwise
  output += map.charAt(63 & block >> 8 - i % 1 * 8) // eslint-disable-line no-bitwise
  ) {
    charCode = str.charCodeAt(i += 3 / 4);

    if (charCode > 0xff) {
      throw new Error('"btoa" failed: The string to be encoded contains characters outside of the Latin1 range.');
    }

    block = block << 8 | charCode; // eslint-disable-line no-bitwise
  }

  return output;
}
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = Math.random() * 16 | 0; // eslint-disable-line no-bitwise

    var v = c === 'x' ? r : r & 0x3 | 0x8; // eslint-disable-line no-bitwise
    return v.toString(16);
  });
}
function validate(object, fields) {
  var invalid = [];
  var emptyFor = {
    object: null,
    string: ''
  };
  var keys = Object.keys(fields);
  keys.forEach(function (key) {
    var type = fields[key];
    // eslint-disable-next-line
    if (_typeof(object[key]) !== type || object[key] === emptyFor[type]) {
      invalid.push(key);
    }
  });
  var missing = '';
  for (var i = 0; i < invalid.length; i += 1) {
    missing += invalid[i] + ', ';
  }
  if (invalid.length > 0) {
    return new Error('fields missing: ' + missing);
  }

  return true;
}

function removeUndefined(value) {
  if (value || !(Object.keys(value).length === 0 && value.constructor === Object)) {
    return JSON.parse(JSON.stringify(value));
  }
  return null;
}

/**
 * Send only when a connection is opened
 * @param {Object} socket
 * @param {Function} callback
 */
function waitForSocketConnection(socket, callback) {
  setTimeout(function () {
    if (socket.readyState === 1) {
      if (callback != null) {
        callback();
      }
    } else {
      waitForSocketConnection(socket, callback);
    }
  }, 5); // wait 5 ms for the connection...
}

function encodeHeaders() {
  var headers = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
  var shouldEncode = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

  // Encode headers
  var encodedHeaders = {};
  if (shouldEncode) {
    Object.keys(headers).forEach(function (header) {
      encodedHeaders[header] = encodeURI(headers[header]);
    });
  } else {
    encodedHeaders = headers;
  }
  return encodedHeaders;
}

/**
 * Returns an instance of Appbase client
 * @param {Object} config To configure properties
 * @param {String} config.url
 * @param {String} config.app
 * @param {String} config.credentials
 * @param {String} config.username
 * @param {String} config.password
 * A callback function which will be invoked before a fetch request made
 */
function AppBase(config) {
  var _URL = URL(config.url || ''),
      _URL$auth = _URL.auth,
      auth = _URL$auth === undefined ? null : _URL$auth,
      _URL$host = _URL.host,
      host = _URL$host === undefined ? '' : _URL$host,
      _URL$path = _URL.path,
      path = _URL$path === undefined ? '' : _URL$path,
      _URL$protocol = _URL.protocol,
      protocol = _URL$protocol === undefined ? '' : _URL$protocol;

  var url = host + path;

  // Validate config and throw appropriate error
  if (typeof url !== 'string' || url === '') {
    throw new Error('URL not present in options.');
  }
  if (typeof config.app !== 'string' || config.app === '') {
    throw new Error('App name is not present in options.');
  }
  if (typeof protocol !== 'string' || protocol === '') {
    throw new Error('Protocol is not present in url. URL should be of the form https://scalr.api.appbase.io');
  }
  // Parse url
  if (url.slice(-1) === '/') {
    url = url.slice(0, -1);
  }
  var credentials = auth || null;
  /**
   * Credentials can be provided as a part of the URL,
   * as username, password args or as a credentials argument directly */
  if (typeof config.credentials === 'string' && config.credentials !== '') {
    // eslint-disable-next-line
    credentials = config.credentials;
  } else if (typeof config.username === 'string' && config.username !== '' && typeof config.password === 'string' && config.password !== '') {
    credentials = config.username + ':' + config.password;
  }

  if (isAppbase(url) && credentials === null) {
    throw new Error('Authentication information is not present. Did you add credentials?');
  }
  this.url = url;
  this.protocol = protocol;
  this.app = config.app;
  this.credentials = credentials;
  this.headers = {};
}

/**
 * To perform fetch request
 * @param {Object} args
 * @param {String} args.method
 * @param {String} args.path
 * @param {Object} args.params
 * @param {Object} args.body
 */
function fetchRequest(args) {
  var _this = this;

  return new Promise(function (resolve, reject) {
    var parsedArgs = removeUndefined(args);
    try {
      var method = parsedArgs.method,
          path = parsedArgs.path,
          params = parsedArgs.params,
          body = parsedArgs.body;

      var bodyCopy = body;
      var contentType = path.endsWith('msearch') || path.endsWith('bulk') ? 'application/x-ndjson' : 'application/json';
      var headers = Object.assign({}, {
        Accept: 'application/json',
        'Content-Type': contentType
      }, _this.headers);
      var timestamp = Date.now();
      if (_this.credentials) {
        headers.Authorization = 'Basic ' + btoa(_this.credentials);
      }
      var requestOptions = {
        method: method,
        headers: headers
      };
      if (Array.isArray(bodyCopy)) {
        var arrayBody = '';
        bodyCopy.forEach(function (item) {
          arrayBody += JSON.stringify(item);
          arrayBody += '\n';
        });

        bodyCopy = arrayBody;
      } else {
        bodyCopy = JSON.stringify(bodyCopy) || {};
      }

      if (Object.keys(bodyCopy).length !== 0) {
        requestOptions.body = bodyCopy;
      }

      var finalRequest = requestOptions;
      if (_this.transformRequest) {
        finalRequest = _this.transformRequest(requestOptions);
      }
      var responseHeaders = {};
      return fetch(_this.protocol + '://' + _this.url + '/' + _this.app + '/' + path + '?' + querystring.stringify(params), finalRequest).then(function (res) {
        res.clone().json().then(function (res2) {
          var allResponses = res2.responses.length;
          console.log(allResponses);
          var errorResponses = res2.responses.filter(function (entry) {
            return entry.hasOwnProperty('error');
          }).length;
          console.log(errorResponses);
          if (allResponses === errorResponses) {
            return reject(res2);
          }
        });
        if (res.status >= 500) {
          return reject(res);
        }
        responseHeaders = res.headers;
        return res.json().then(function (data) {
          if (res.status >= 400) {
            return reject(res);
          }
          var response = Object.assign({}, data, {
            _timestamp: timestamp,
            _headers: responseHeaders
          });
          return resolve(response);
        });
      }).catch(function (e) {
        return reject(e);
      });
    } catch (e) {
      return reject(e);
    }
  });
}

var WebSocket = typeof window !== 'undefined' ? window.WebSocket : require('ws');

/**
 * To connect a web socket
 * @param {Object} args
 * @param {String} args.method
 * @param {String} args.path
 * @param {Object} args.params
 * @param {Object} args.body
 */
function wsRequest(args, onData, onError, onClose) {
  var _this = this;

  try {
    var parsedArgs = removeUndefined(args);
    var method = parsedArgs.method,
        path = parsedArgs.path,
        params = parsedArgs.params;

    var bodyCopy = args.body;
    if (!bodyCopy || (typeof bodyCopy === 'undefined' ? 'undefined' : _typeof(bodyCopy)) !== 'object') {
      bodyCopy = {};
    }
    var init = function init() {
      _this.ws = new WebSocket('wss://' + _this.url + '/' + _this.app);
      _this.id = uuidv4();

      _this.request = {
        id: _this.id,
        path: _this.app + '/' + path + '?' + querystring.stringify(params),
        method: method,
        body: bodyCopy
      };
      if (_this.credentials) {
        _this.request.authorization = 'Basic ' + btoa(_this.credentials);
      }
      _this.result = {};
      _this.closeHandler = function () {
        _this.wsClosed();
      };
      _this.errorHandler = function (err) {
        _this.processError.apply(_this, [err]);
      };
      _this.messageHandler = function (message) {
        var dataObj = JSON.parse(message.data);
        if (dataObj.body && dataObj.body.status >= 400) {
          _this.processError.apply(_this, [dataObj]);
        } else {
          _this.processMessage.apply(_this, [dataObj]);
        }
      };
      _this.send = function (request) {
        waitForSocketConnection(_this.ws, function () {
          try {
            _this.ws.send(JSON.stringify(request));
          } catch (e) {
            console.warn(e);
          }
        });
      };
      _this.ws.onmessage = _this.messageHandler;
      _this.ws.onerror = _this.errorHandler;
      _this.ws.onclose = _this.closeHandler;
      _this.send(_this.request);
      _this.result.stop = _this.stop;
      _this.result.reconnect = _this.reconnect;

      return _this.result;
    };
    this.wsClosed = function () {
      if (onClose) {
        onClose();
      }
    };
    this.stop = function () {
      _this.ws.onmessage = undefined;
      _this.ws.onclose = undefined;
      _this.ws.onerror = undefined;
      _this.wsClosed();
      var unsubRequest = JSON.parse(JSON.stringify(_this.request));
      unsubRequest.unsubscribe = true;

      if (_this.unsubscribed !== true) {
        _this.send(unsubRequest);
      }

      _this.unsubscribed = true;
    };
    this.reconnect = function () {
      _this.stop();
      return wsRequest(args, onData, onError, onClose);
    };
    this.processError = function (err) {
      if (onError) {
        onError(err);
      } else {
        console.warn(err);
      }
    };

    this.processMessage = function (origDataObj) {
      var dataObj = JSON.parse(JSON.stringify(origDataObj));
      if (!dataObj.id && dataObj.message) {
        if (onError) {
          onError(dataObj);
        }
        return;
      }

      if (dataObj.id === _this.id) {
        if (dataObj.message) {
          delete dataObj.id;
          if (onError) {
            onError(dataObj);
          }
          return;
        }

        if (dataObj.query_id) {
          _this.query_id = dataObj.query_id;
        }

        if (dataObj.channel) {
          _this.channel = dataObj.channel;
        }

        if (dataObj.body && dataObj.body !== '') {
          if (onData) {
            onData(dataObj.body);
          }
        }

        return;
      }

      if (!dataObj.id && dataObj.channel && dataObj.channel === _this.channel) {
        if (onData) {
          onData(dataObj.event);
        }
      }
    };
    return init();
  } catch (e) {
    if (onError) {
      onError(e);
    } else {
      console.warn(e);
    }
    return null;
  }
}

/**
 * Index Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 * @param {String} args.id
 */
function indexApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    type: 'string',
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }
  var type = parsedArgs.type,
      id = parsedArgs.id,
      body = parsedArgs.body;


  delete parsedArgs.type;
  delete parsedArgs.body;
  delete parsedArgs.id;

  var path = void 0;
  if (id) {
    path = type + '/' + encodeURIComponent(id);
  } else {
    path = type;
  }
  return this.performFetchRequest({
    method: 'POST',
    path: path,
    params: parsedArgs,
    body: body
  });
}

/**
 * Get Service
 * @param {Object} args
 * @param {String} args.type
 * @param {String} args.id
 */
function getApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    type: 'string',
    id: 'string'
  });

  if (valid !== true) {
    throw valid;
  }

  var type = parsedArgs.type,
      id = parsedArgs.id;


  delete parsedArgs.type;
  delete parsedArgs.id;

  var path = type + '/' + encodeURIComponent(id);

  return this.performFetchRequest({
    method: 'GET',
    path: path,
    params: parsedArgs
  });
}

/**
 * Update Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 * @param {String} args.id
 */
function updateApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    type: 'string',
    id: 'string',
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  var type = parsedArgs.type,
      id = parsedArgs.id,
      body = parsedArgs.body;

  delete parsedArgs.type;
  delete parsedArgs.id;
  delete parsedArgs.body;
  var path = type + '/' + encodeURIComponent(id) + '/_update';

  return this.performFetchRequest({
    method: 'POST',
    path: path,
    params: parsedArgs,
    body: body
  });
}

/**
 * Delete Service
 * @param {Object} args
 * @param {String} args.type
 * @param {String} args.id
 */
function deleteApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    type: 'string',
    id: 'string'
  });
  if (valid !== true) {
    throw valid;
  }

  var type = parsedArgs.type,
      id = parsedArgs.id;

  delete parsedArgs.type;
  delete parsedArgs.id;

  var path = type + '/' + encodeURIComponent(id);

  return this.performFetchRequest({
    method: 'DELETE',
    path: path,
    params: parsedArgs
  });
}

/**
 * Bulk Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 */
function bulkApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  var type = parsedArgs.type,
      body = parsedArgs.body;


  delete parsedArgs.type;
  delete parsedArgs.body;

  var path = void 0;
  if (type) {
    path = type + '/_bulk';
  } else {
    path = '/_bulk';
  }

  return this.performFetchRequest({
    method: 'POST',
    path: path,
    params: parsedArgs,
    body: body
  });
}

/**
 * Search Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 */
function searchApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  var type = void 0;
  if (Array.isArray(parsedArgs.type)) {
    type = parsedArgs.type.join();
  } else {
    // eslint-disable-next-line
    type = parsedArgs.type;
  }

  var body = parsedArgs.body;


  delete parsedArgs.type;
  delete parsedArgs.body;

  var path = void 0;
  if (type) {
    path = type + '/_search';
  } else {
    path = '_search';
  }

  return this.performFetchRequest({
    method: 'POST',
    path: path,
    params: parsedArgs,
    body: body
  });
}

/**
 * Msearch Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 */
function msearchApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  var type = void 0;
  if (Array.isArray(parsedArgs.type)) {
    type = parsedArgs.type.join();
  } else {
    type = parsedArgs.type;
  }

  var body = parsedArgs.body;


  delete parsedArgs.type;
  delete parsedArgs.body;

  var path = void 0;
  if (type) {
    path = type + '/_msearch';
  } else {
    path = '_msearch';
  }

  return this.performFetchRequest({
    method: 'POST',
    path: path,
    params: parsedArgs,
    body: body
  });
}

/**
 * Stream Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Boolean} args.stream
 * @param {String} args.id
 * @param {Function} onData
 * @param {Function} onError
 * @param {Function} onClose
 */
function getStream(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    type: 'string',
    id: 'string'
  });
  if (valid !== true) {
    throw valid;
  }

  var type = parsedArgs.type,
      id = parsedArgs.id;


  delete parsedArgs.type;
  delete parsedArgs.id;
  delete parsedArgs.stream;

  if (parsedArgs.stream === true) {
    parsedArgs.stream = 'true';
  } else {
    delete parsedArgs.stream;
    parsedArgs.streamonly = 'true';
  }

  for (var _len = arguments.length, rest = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
    rest[_key - 1] = arguments[_key];
  }

  return this.performWsRequest.apply(this, [{
    method: 'GET',
    path: type + '/' + encodeURIComponent(id),
    params: parsedArgs
  }].concat(rest));
}

/**
 * Search Stream
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 * @param {Boolean} args.stream
 * @param {Function} onData
 * @param {Function} onError
 * @param {Function} onClose
 */
function searchStreamApi(args) {
  var parsedArgs = removeUndefined(args);
  // Validate arguments
  var valid = validate(parsedArgs, {
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  if (parsedArgs.type === undefined || Array.isArray(parsedArgs.type) && parsedArgs.type.length === 0) {
    throw new Error('Missing fields: type');
  }

  var type = void 0;
  if (Array.isArray(parsedArgs.type)) {
    type = parsedArgs.type.join();
  } else {
    type = parsedArgs.type;
  }

  var body = parsedArgs.body;

  delete parsedArgs.type;
  delete parsedArgs.body;
  delete parsedArgs.stream;

  parsedArgs.streamonly = 'true';

  for (var _len = arguments.length, rest = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
    rest[_key - 1] = arguments[_key];
  }

  return this.performWsRequest.apply(this, [{
    method: 'POST',
    path: type + '/_search',
    params: parsedArgs,
    body: body
  }].concat(rest));
}

/**
 * Webhook Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 * @param {Object} webhook
 * @param {Function} onData
 * @param {Function} onError
 * @param {Function} onClose
 */
function searchStreamToURLApi(args, webhook) {
  for (var _len = arguments.length, rest = Array(_len > 2 ? _len - 2 : 0), _key = 2; _key < _len; _key++) {
    rest[_key - 2] = arguments[_key];
  }

  var _this = this;

  var parsedArgs = removeUndefined(args);
  var bodyCopy = parsedArgs.body;
  var type = void 0;
  var typeString = void 0;
  // Validate arguments
  var valid = validate(parsedArgs, {
    body: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  if (parsedArgs.type === undefined || !(typeof parsedArgs.type === 'string' || Array.isArray(parsedArgs.type)) || parsedArgs.type === '' || parsedArgs.type.length === 0) {
    throw new Error('fields missing: type');
  }

  valid = validate(parsedArgs.body, {
    query: 'object'
  });
  if (valid !== true) {
    throw valid;
  }

  if (Array.isArray(parsedArgs.type)) {
    type = parsedArgs.type;

    typeString = parsedArgs.type.join();
  } else {
    type = [parsedArgs.type];
    typeString = parsedArgs.type;
  }

  var webhooks = [];
  var _bodyCopy = bodyCopy,
      query = _bodyCopy.query;


  if (typeof webhook === 'string') {
    var webHookObj = {};
    webHookObj.url = webhook;
    webHookObj.method = 'GET';
    webhooks.push(webHookObj);
  } else if (webhook.constructor === Array) {
    webhooks = webhook;
  } else if (webhook === Object(webhook)) {
    webhooks.push(webhook);
  } else {
    throw new Error('fields missing: second argument(webhook) is necessary');
  }

  var populateBody = function populateBody() {
    bodyCopy = {};
    bodyCopy.webhooks = webhooks;
    bodyCopy.query = query;
    bodyCopy.type = type;
  };

  populateBody();

  var encode64 = btoa(stringify(query));
  var path = '.percolator/webhooks-0-' + typeString + '-0-' + encode64;

  this.change = function () {
    webhooks = [];

    if (typeof parsedArgs === 'string') {
      var webhook2 = {};
      webhook2.url = parsedArgs;
      webhook2.method = 'POST';
      webhooks.push(webhook2);
    } else if (parsedArgs.constructor === Array) {
      webhooks = parsedArgs;
    } else if (parsedArgs === Object(parsedArgs)) {
      webhooks.push(parsedArgs);
    } else {
      throw new Error('fields missing: one of webhook or url fields is required');
    }

    populateBody();

    return _this.performRequest('POST');
  };
  this.stop = function () {
    bodyCopy = undefined;
    return _this.performRequest('DELETE');
  };
  this.performRequest = function (method) {
    var res = _this.performWsRequest.apply(_this, [{
      method: method,
      path: path,
      body: bodyCopy
    }].concat(rest));

    res.change = _this.change;
    res.stop = _this.stop;

    return res;
  };
  return this.performRequest('POST');
}

/**
 * To get types
 */
function getTypesService() {
  var _this = this;

  return new Promise(function (resolve, reject) {
    try {
      return _this.performFetchRequest({
        method: 'GET',
        path: '_mapping'
      }).then(function (data) {
        var types = Object.keys(data[_this.app].mappings).filter(function (type) {
          return type !== '_default_';
        });
        return resolve(types);
      });
    } catch (e) {
      return reject(e);
    }
  });
}

/**
 * To get mappings
 */
function getMappings() {
  return this.performFetchRequest({
    method: 'GET',
    path: '_mapping'
  });
}

function index (config) {
  var client = new AppBase(config);

  AppBase.prototype.performFetchRequest = fetchRequest;

  AppBase.prototype.performWsRequest = wsRequest;

  AppBase.prototype.index = indexApi;

  AppBase.prototype.get = getApi;

  AppBase.prototype.update = updateApi;

  AppBase.prototype.delete = deleteApi;

  AppBase.prototype.bulk = bulkApi;

  AppBase.prototype.search = searchApi;

  AppBase.prototype.msearch = msearchApi;

  AppBase.prototype.getStream = getStream;

  AppBase.prototype.searchStream = searchStreamApi;

  AppBase.prototype.searchStreamToURL = searchStreamToURLApi;

  AppBase.prototype.getTypes = getTypesService;

  AppBase.prototype.getMappings = getMappings;

  AppBase.prototype.setHeaders = function () {
    var headers = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
    var shouldEncode = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

    // Encode headers
    if (shouldEncode) {
      this.headers = encodeHeaders(headers);
    } else {
      this.headers = headers;
    }
  };

  if (typeof window !== 'undefined') {
    window.Appbase = client;
  }
  return client;
}

module.exports = index;
