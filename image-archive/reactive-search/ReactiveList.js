'use strict';

exports.__esModule = true;

var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

var _react = require('react');

var _react2 = _interopRequireDefault(_react);

var _actions = require('@appbaseio/reactivecore/lib/actions');

var _helper = require('@appbaseio/reactivecore/lib/utils/helper');

var _types = require('@appbaseio/reactivecore/lib/utils/types');

var _types2 = _interopRequireDefault(_types);

var _Pagination = require('./addons/Pagination');

var _Pagination2 = _interopRequireDefault(_Pagination);

var _PoweredBy = require('./addons/PoweredBy');

var _PoweredBy2 = _interopRequireDefault(_PoweredBy);

var _Flex = require('../../styles/Flex');

var _Flex2 = _interopRequireDefault(_Flex);

var _results = require('../../styles/results');

var _utils = require('../../utils');

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _objectWithoutProperties(obj, keys) { var target = {}; for (var i in obj) { if (keys.indexOf(i) >= 0) continue; if (!Object.prototype.hasOwnProperty.call(obj, i)) continue; target[i] = obj[i]; } return target; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var ReactiveList = function (_Component) {
	_inherits(ReactiveList, _Component);

	function ReactiveList(props) {
		_classCallCheck(this, ReactiveList);

		var _this = _possibleConstructorReturn(this, _Component.call(this, props));

		_initialiseProps.call(_this);

		var currentPage = 0;
		if (_this.props.defaultPage >= 0) {
			currentPage = _this.props.defaultPage;
		} else if (_this.props.currentPage) {
			currentPage = Math.max(_this.props.currentPage - 1, 0);
		}
		_this.initialFrom = currentPage * props.size; // used for page resetting on query change
		_this.state = {
			from: _this.initialFrom,
			currentPage: currentPage
		};
		_this.internalComponent = props.componentId + '__internal';
		props.setQueryListener(props.componentId, props.onQueryChange, props.onError);
		return _this;
	}

	ReactiveList.prototype.componentDidMount = function componentDidMount() {
		this.props.addComponent(this.internalComponent);
		this.props.addComponent(this.props.componentId);

		if (this.props.stream) {
			this.props.setStreaming(this.props.componentId, true);
		}

		var options = (0, _helper.getQueryOptions)(this.props);
		options.from = this.state.from;
		if (this.props.sortOptions) {
			var _ref;

			options.sort = [(_ref = {}, _ref[this.props.sortOptions[0].dataField] = {
				order: this.props.sortOptions[0].sortBy
			}, _ref)];
		} else if (this.props.sortBy) {
			var _ref2;

			options.sort = [(_ref2 = {}, _ref2[this.props.dataField] = {
				order: this.props.sortBy
			}, _ref2)];
		}

		// Override sort query with defaultQuery's sort if defined
		this.defaultQuery = null;
		if (this.props.defaultQuery) {
			this.defaultQuery = this.props.defaultQuery();
			if (this.defaultQuery.sort) {
				options.sort = this.defaultQuery.sort;
			}
		}

		var _ref3 = this.defaultQuery || {},
		    sort = _ref3.sort,
		    query = _objectWithoutProperties(_ref3, ['sort']);

		// execute is set to false at the time of mount
		// to avoid firing (multiple) partial queries.
		// Hence we are building the query in parts here
		// and only executing it with setReact() at core


		var execute = false;

		this.props.setQueryOptions(this.props.componentId, options, execute);

		if (this.defaultQuery) {
			this.props.updateQuery({
				componentId: this.internalComponent,
				query: query
			}, execute);
		} else {
			this.props.updateQuery({
				componentId: this.internalComponent,
				query: null
			}, execute);
		}

		// query will be executed here
		this.setReact(this.props);

		this.domNode = window;
		if (!this.props.pagination) {
			var scrollTarget = this.props.scrollTarget;

			if (scrollTarget) {
				this.domNode = document.getElementById(scrollTarget);
			}
			this.domNode.addEventListener('scroll', this.scrollHandler);
		}
	};

	ReactiveList.prototype.componentWillReceiveProps = function componentWillReceiveProps(nextProps) {
		var _this2 = this;

		var totalPages = Math.ceil(nextProps.total / nextProps.size) || 0;

		if (!(0, _helper.isEqual)(this.props.sortOptions, nextProps.sortOptions) || this.props.sortBy !== nextProps.sortBy || this.props.size !== nextProps.size || !(0, _helper.isEqual)(this.props.dataField, nextProps.dataField) || !(0, _helper.isEqual)(this.props.includeFields, nextProps.includeFields) || !(0, _helper.isEqual)(this.props.excludeFields, nextProps.excludeFields)) {
			var options = (0, _helper.getQueryOptions)(nextProps);
			options.from = this.state.from;
			if (nextProps.sortOptions) {
				var _ref4;

				options.sort = [(_ref4 = {}, _ref4[nextProps.sortOptions[0].dataField] = {
					order: nextProps.sortOptions[0].sortBy
				}, _ref4)];
			} else if (nextProps.sortBy) {
				var _ref5;

				options.sort = [(_ref5 = {}, _ref5[nextProps.dataField] = {
					order: nextProps.sortBy
				}, _ref5)];
			}
			this.props.setQueryOptions(this.props.componentId, options, true);
		}

		if (nextProps.defaultQuery && !(0, _helper.isEqual)(nextProps.defaultQuery(), this.defaultQuery)) {
			var _options = (0, _helper.getQueryOptions)(nextProps);
			_options.from = 0;
			this.defaultQuery = nextProps.defaultQuery();

			var _defaultQuery = this.defaultQuery,
			    sort = _defaultQuery.sort,
			    query = _objectWithoutProperties(_defaultQuery, ['sort']);

			if (sort) {
				_options.sort = this.defaultQuery.sort;
				nextProps.setQueryOptions(nextProps.componentId, _options, !query);
			}

			this.props.updateQuery({
				componentId: this.internalComponent,
				query: query
			}, true);

			// reset page because of query change
			this.setState({
				currentPage: 0,
				from: 0
			}, function () {
				_this2.updatePageURL(0);
			});
		}

		if (this.props.stream !== nextProps.stream) {
			this.props.setStreaming(nextProps.componentId, nextProps.stream);
		}

		if (!(0, _helper.isEqual)(nextProps.react, this.props.react)) {
			this.setReact(nextProps);
		}

		if (this.props.pagination) {
			// called when page is changed
			if (this.props.isLoading && (this.props.hits || nextProps.hits)) {
				if (nextProps.onPageChange) {
					nextProps.onPageChange(this.state.currentPage + 1, totalPages);
				} else {
					this.domNode.scrollTo(0, 0);
				}
			}

			if (this.props.currentPage !== nextProps.currentPage && nextProps.currentPage > 0 && nextProps.currentPage <= totalPages) {
				this.setPage(nextProps.currentPage - 1);
			}
		}

		if (!nextProps.pagination) {
			if (this.props.hits && nextProps.hits) {
				if (this.props.hits.length !== nextProps.hits.length || nextProps.hits.length === nextProps.total) {
					if (nextProps.hits.length < this.props.hits.length) {
						// query has changed
						this.domNode.scrollTo(0, 0);
						this.setState({
							from: 0
						});
					}
				}
			}
		}

		if (nextProps.queryLog && this.props.queryLog && nextProps.queryLog !== this.props.queryLog) {
			// usecase:
			// - query has changed from non-null prev query

			if (nextProps.queryLog.from !== this.state.from) {
				// query's 'from' key doesn't match the state's 'from' key,
				// i.e. this query change was not triggered by the page change (loadMore)
				this.setState({
					currentPage: 0
				}, function () {
					_this2.updatePageURL(0);
				});

				if (nextProps.onPageChange) {
					nextProps.onPageChange(1, totalPages);
				}
			} else if (this.initialFrom && this.initialFrom === nextProps.queryLog.from) {
				// [non-zero] initialFrom matches the current query's from
				// but the query has changed

				// we need to update the query options in this case
				// because the initial load had set the query 'from' in the store
				// which is not valid anymore because the query has changed
				var _options2 = (0, _helper.getQueryOptions)(nextProps);
				_options2.from = 0;
				this.initialFrom = 0;

				if (nextProps.sortOptions) {
					var _ref6;

					_options2.sort = [(_ref6 = {}, _ref6[nextProps.sortOptions[0].dataField] = {
						order: nextProps.sortOptions[0].sortBy
					}, _ref6)];
				} else if (nextProps.sortBy) {
					var _ref7;

					_options2.sort = [(_ref7 = {}, _ref7[nextProps.dataField] = {
						order: nextProps.sortBy
					}, _ref7)];
				}

				this.props.setQueryOptions(this.props.componentId, _options2, true);
			}
		}

		if (nextProps.pagination !== this.props.pagination) {
			if (nextProps.pagination) {
				this.domNode.addEventListener('scroll', this.scrollHandler);
			} else {
				this.domNode.removeEventListener('scroll', this.scrollHandler);
			}
		}

		// handle window url history change (on native back and forth interactions)
		if (this.state.currentPage !== nextProps.defaultPage && this.props.defaultPage !== nextProps.defaultPage) {
			this.setPage(nextProps.defaultPage >= 0 ? nextProps.defaultPage : 0);
		}
	};

	ReactiveList.prototype.componentWillUnmount = function componentWillUnmount() {
		this.props.removeComponent(this.props.componentId);
		this.props.removeComponent(this.internalComponent);

		if (this.domNode) {
			this.domNode.removeEventListener('scroll', this.scrollHandler);
		}
	};

	// only used for SSR


	ReactiveList.prototype.render = function render() {
		var _this3 = this;

		var _props = this.props,
		    onData = _props.onData,
		    size = _props.size;
		var currentPage = this.state.currentPage;

		var results = (0, _helper.parseHits)(this.props.hits) || [];
		var streamResults = (0, _helper.parseHits)(this.props.streamHits) || [];
		var filteredResults = results;

		if (streamResults.length) {
			var ids = streamResults.map(function (item) {
				return item._id;
			});
			filteredResults = filteredResults.filter(function (item) {
				return !ids.includes(item._id);
			});
		}

		return _react2.default.createElement(
			'div',
			{ style: this.props.style, className: this.props.className },
			this.props.isLoading && this.props.pagination && this.props.loader,
			_react2.default.createElement(
				_Flex2.default,
				{
					labelPosition: this.props.sortOptions ? 'right' : 'left',
					className: (0, _helper.getClassName)(this.props.innerClass, 'resultsInfo')
				},
				this.props.sortOptions ? this.renderSortOptions() : null,
				this.props.showResultStats ? this.renderResultStats() : null
			),
			!this.props.isLoading && results.length === 0 && streamResults.length === 0 ? this.renderNoResults() : null,
			this.props.pagination && (this.props.paginationAt === 'top' || this.props.paginationAt === 'both') ? _react2.default.createElement(_Pagination2.default, {
				pages: this.props.pages,
				totalPages: Math.ceil(this.props.total / this.props.size),
				currentPage: this.state.currentPage,
				setPage: this.setPage,
				innerClass: this.props.innerClass,
				fragmentName: this.props.componentId
			}) : null,
			this.props.onAllData ? this.props.onAllData(results, streamResults, this.loadMore, {
				base: currentPage * size,
				triggerClickAnalytics: this.triggerClickAnalytics
			}) : _react2.default.createElement(
				'div',
				{
					className: this.props.listClass + ' ' + (0, _helper.getClassName)(this.props.innerClass, 'list')
				},
				[].concat(streamResults, filteredResults).map(function (item, index) {
					return onData(item, function () {
						return _this3.triggerClickAnalytics(currentPage * size + index);
					});
				})
			),
			this.props.isLoading && !this.props.pagination ? this.props.loader || _react2.default.createElement(
				'div',
				{
					style: {
						textAlign: 'center',
						margin: '20px 0',
						color: '#666'
					}
				},
				'Loading...'
			) // prettier-ignore
			: null,
			this.props.pagination && (this.props.paginationAt === 'bottom' || this.props.paginationAt === 'both') ? _react2.default.createElement(_Pagination2.default, {
				pages: this.props.pages,
				totalPages: Math.ceil(this.props.total / this.props.size),
				currentPage: this.state.currentPage,
				setPage: this.setPage,
				innerClass: this.props.innerClass,
				fragmentName: this.props.componentId
			}) : null,
			this.props.config.url.endsWith('appbase.io') && results.length ? _react2.default.createElement(
				_Flex2.default,
				{
					direction: 'row-reverse',
					className: (0, _helper.getClassName)(this.props.innerClass, 'poweredBy')
				},
				_react2.default.createElement(_PoweredBy2.default, null)
			) : null
		);
	};

	return ReactiveList;
}(_react.Component);

ReactiveList.generateQueryOptions = function (props) {
	var options = {};
	options.from = props.currentPage ? (props.currentPage - 1) * (props.size || 10) : 0;
	options.size = props.size || 10;

	if (props.sortOptions) {
		var _ref8;

		options.sort = [(_ref8 = {}, _ref8[props.sortOptions[0].dataField] = {
			order: props.sortOptions[0].sortBy
		}, _ref8)];
	} else if (props.sortBy) {
		var _ref9;

		options.sort = [(_ref9 = {}, _ref9[props.dataField] = {
			order: props.sortBy
		}, _ref9)];
	}

	return options;
};

var _initialiseProps = function _initialiseProps() {
	var _this4 = this;

	this.setReact = function (props) {
		var react = props.react;

		if (react) {
			var newReact = (0, _helper.pushToAndClause)(react, _this4.internalComponent);
			props.watchComponent(props.componentId, newReact);
		} else {
			props.watchComponent(props.componentId, {
				and: _this4.internalComponent
			});
		}
	};

	this.scrollHandler = function () {
		var renderLoader = window.innerHeight + window.pageYOffset + 300 >= document.body.offsetHeight;
		if (_this4.props.scrollTarget) {
			renderLoader = _this4.domNode.clientHeight + _this4.domNode.scrollTop + 300 >= _this4.domNode.scrollHeight;
		}
		if (!_this4.props.isLoading && renderLoader) {
			_this4.loadMore();
		}
	};

	this.loadMore = function () {
		if (_this4.props.hits && !_this4.props.pagination && _this4.props.total !== _this4.props.hits.length) {
			var value = _this4.state.from + _this4.props.size;
			var options = (0, _helper.getQueryOptions)(_this4.props);

			_this4.setState({
				from: value
			});
			_this4.props.loadMore(_this4.props.componentId, _extends({}, options, {
				from: value
			}), true);
		}
	};

	this.setPage = function (page) {
		// onPageClick will be called everytime a pagination button is clicked
		if (page !== _this4.state.currentPage) {
			var onPageClick = _this4.props.onPageClick;

			if (onPageClick) {
				onPageClick(page + 1);
			}
			var value = _this4.props.size * page;
			var options = (0, _helper.getQueryOptions)(_this4.props);
			options.from = _this4.state.from;
			_this4.setState({
				from: value,
				currentPage: page
			}, function () {
				_this4.props.loadMore(_this4.props.componentId, _extends({}, options, {
					from: value
				}), false);

				_this4.updatePageURL(page);
			});
		}
	};

	this.renderResultStats = function () {
		//import * as util from 'util' // has no default export
		//import { inspect } from 'util' // or directly
		// or 
		var util = require('util');
		if (_this4.props.onResultStats && _this4.props.total) {
			return _this4.props.onResultStats(_this4.props.total, _this4.props.time);
		} else if (_this4.props.total) {
			var data = _this4.props.queryLog;
			data.aggs = {"exam_count" : {"cardinality" : {"field" : "AccessionNumber.keyword"} }, "patient_count" : {"cardinality" : {"field" : "PatientID.keyword"} } };

			var _props2 = _this4.props, config = _props2.config, searchId = _props2.analytics.searchId;
			var url = config.url, app = config.app, credentials = config.credentials;

			var merging_url = [url, app, '/image/_search'];
			var full_url = merging_url.join('/').replace(/([^:]\/)\/+/g, "$1");
			fetch (full_url, {
              method: 'POST', // or 'PUT'
              body: JSON.stringify(data), // data can be `string` or {object}!
              headers:{
                'Content-Type': 'application/json'
              }
            })

			.then(function(response) {
                return response.json();
              })
              .then(function(response) {
                var str = [_this4.props.total.toLocaleString(),
                                ' results, ',
                                response.aggregations.exam_count.value.toLocaleString(),
                                ' exams, ',
                                response.aggregations.patient_count.value.toLocaleString(),
                                ' patients found in ',
                                _this4.props.time.toLocaleString(),
                                'ms'].join('');
                var div = document.getElementsByClassName('result-list-info')[0];
                div.innerHTML = str;
                div.className += " result-stats ";


			return _react2.default.createElement(
				'p',
{
                  className: _results.resultStats + ' ' + (0, _helper.getClassName)(_this4.props.innerClass, 'resultStats')
                },
                str
              );
        });
    }
    return null;
  };;

	this.renderNoResults = function () {
		if (typeof document !== 'undefined') {
		          var div = document.getElementsByClassName('result-list-info')[0];
		          div.innerHTML = '';
		      }
		    return _react2.default.createElement(
		      'p',
		      { className: (0, _helper.getClassName)(_this4.props.innerClass, 'noResults') || null },
		      _this4.props.onNoResults
		    );
		  };

	this.handleSortChange = function (e) {
		var _ref10;

		var index = e.target.value;
		var options = (0, _helper.getQueryOptions)(_this4.props);
		// This fixes issue #371 (where sorting a multi-result page with infinite loader breaks)
		options.from = 0;

		options.sort = [(_ref10 = {}, _ref10[_this4.props.sortOptions[index].dataField] = {
			order: _this4.props.sortOptions[index].sortBy
		}, _ref10)];
		_this4.props.setQueryOptions(_this4.props.componentId, options, true);

		_this4.setState({
			currentPage: 0,
			from: 0
		}, function () {
			_this4.updatePageURL(0);
		});
	};

	this.updatePageURL = function (page) {
		if (_this4.props.URLParams) {
			_this4.props.setPageURL(_this4.props.componentId, page + 1, _this4.props.componentId, false, true);
		}
	};

	this.triggerClickAnalytics = function (searchPosition) {
		// click analytics would only work client side and after javascript loads
		var _props2 = _this4.props,
		    config = _props2.config,
		    searchId = _props2.analytics.searchId;
		var url = config.url,
		    app = config.app,
		    credentials = config.credentials;

		if (config.analytics && url.endsWith('scalr.api.appbase.io') && searchId) {
			fetch(url + '/' + app + '/analytics', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: 'Basic ' + btoa(credentials),
					'X-Search-Id': searchId,
					'X-Search-Click': true,
					'X-Search-Click-Position': searchPosition + 1
				}
			});
		}
	};

	this.renderSortOptions = function () {
		return _react2.default.createElement(
			'select',
			{
				className: _results.sortOptions + ' ' + (0, _helper.getClassName)(_this4.props.innerClass, 'sortOptions'),
				name: 'sort-options',
				onChange: _this4.handleSortChange
			},
			_this4.props.sortOptions.map(function (sort, index) {
				return _react2.default.createElement(
					'option',
					{ key: sort.label, value: index },
					sort.label
				);
			})
		);
	};
};

ReactiveList.propTypes = {
	addComponent: _types2.default.funcRequired,
	loadMore: _types2.default.funcRequired,
	removeComponent: _types2.default.funcRequired,
	setQueryListener: _types2.default.funcRequired,
	onQueryChange: _types2.default.func,
	onError: _types2.default.func,
	setPageURL: _types2.default.func,
	setQueryOptions: _types2.default.funcRequired,
	setStreaming: _types2.default.func,
	updateQuery: _types2.default.funcRequired,
	watchComponent: _types2.default.funcRequired,
	currentPage: _types2.default.number,
	hits: _types2.default.hits,
	isLoading: _types2.default.bool,
	includeFields: _types2.default.includeFields,
	streamHits: _types2.default.hits,
	time: _types2.default.number,
	total: _types2.default.number,
	config: _types2.default.props,
	analytics: _types2.default.props,
	queryLog: _types2.default.props,
	// component props
	className: _types2.default.string,
	componentId: _types2.default.stringRequired,
	dataField: _types2.default.stringRequired,
	defaultPage: _types2.default.number,
	defaultQuery: _types2.default.func,
	excludeFields: _types2.default.excludeFields,
	innerClass: _types2.default.style,
	listClass: _types2.default.string,
	loader: _types2.default.title,
	onAllData: _types2.default.func,
	onData: _types2.default.func,
	onNoResults: _types2.default.title,
	onPageChange: _types2.default.func,
	onPageClick: _types2.default.func,
	onResultStats: _types2.default.func,
	pages: _types2.default.number,
	pagination: _types2.default.bool,
	paginationAt: _types2.default.paginationAt,
	react: _types2.default.react,
	scrollTarget: _types2.default.string,
	showResultStats: _types2.default.bool,
	size: _types2.default.number,
	sortBy: _types2.default.sortBy,
	sortOptions: _types2.default.sortOptions,
	stream: _types2.default.bool,
	style: _types2.default.style,
	URLParams: _types2.default.bool
};

ReactiveList.defaultProps = {
	className: null,
	currentPage: 0,
	listClass: '',
	pages: 5,
	pagination: false,
	paginationAt: 'bottom',
	includeFields: ['*'],
	excludeFields: [],
	showResultStats: true,
	size: 10,
	style: {},
	URLParams: false,
	onNoResults: 'No Results found.'
};

var mapStateToProps = function mapStateToProps(state, props) {
	return {
		defaultPage: state.selectedValues[props.componentId] && state.selectedValues[props.componentId].value - 1 || -1,
		hits: state.hits[props.componentId] && state.hits[props.componentId].hits,
		isLoading: state.isLoading[props.componentId] || false,
		streamHits: state.streamHits[props.componentId],
		time: state.hits[props.componentId] && state.hits[props.componentId].time || 0,
		total: state.hits[props.componentId] && state.hits[props.componentId].total,
		analytics: state.analytics,
		config: state.config,
		queryLog: state.queryLog[props.componentId]
	};
};

var mapDispatchtoProps = function mapDispatchtoProps(dispatch) {
	return {
		addComponent: function addComponent(component) {
			return dispatch((0, _actions.addComponent)(component));
		},
		loadMore: function loadMore(component, options, append) {
			return dispatch((0, _actions.loadMore)(component, options, append));
		},
		removeComponent: function removeComponent(component) {
			return dispatch((0, _actions.removeComponent)(component));
		},
		setPageURL: function setPageURL(component, value, label, showFilter, URLParams) {
			return dispatch((0, _actions.setValue)(component, value, label, showFilter, URLParams));
		},
		setQueryOptions: function setQueryOptions(component, props, execute) {
			return dispatch((0, _actions.setQueryOptions)(component, props, execute));
		},
		setQueryListener: function setQueryListener(component, onQueryChange, beforeQueryChange) {
			return dispatch((0, _actions.setQueryListener)(component, onQueryChange, beforeQueryChange));
		},
		setStreaming: function setStreaming(component, stream) {
			return dispatch((0, _actions.setStreaming)(component, stream));
		},
		updateQuery: function updateQuery(updateQueryObject, execute) {
			return dispatch((0, _actions.updateQuery)(updateQueryObject, execute));
		},
		watchComponent: function watchComponent(component, react) {
			return dispatch((0, _actions.watchComponent)(component, react));
		}
	};
};

exports.default = (0, _utils.connect)(mapStateToProps, mapDispatchtoProps)(ReactiveList);