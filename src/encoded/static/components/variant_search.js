'use strict';
import Iframe from 'react-iframe';
var React = require('react');
import PropTypes from 'prop-types';
import createReactClass from 'create-react-class';
var queryString = require('query-string');
var button = require('../libs/bootstrap/button');
var {Modal, ModalHeader, ModalBody, ModalFooter} = require('../libs/bootstrap/modal');
var panel = require('../libs/bootstrap/panel');
var globals = require('./globals');
var fetched = require('./fetched');
var url = require('url');
var search = require('./search');
var button = require('../libs/bootstrap/button');
var dropdownMenu = require('../libs/bootstrap/dropdown-menu');
import { TabPanel, TabPanelPane } from '../libs/bootstrap/panel';
var FacetList = search.FacetList;
var Facet = search.Facet;
var TextFilter = search.TextFilter;
var BatchDownload = search.BatchDownload;
var FetchedData = fetched.FetchedData;
var Param = fetched.Param;
var DropdownButton = button.DropdownButton;
var DropdownMenu = dropdownMenu.DropdownMenu;
var {Panel, PanelBody, PanelHeading} = panel;
var { FileGallery } = require('./anno_viz');
var regionGenomes = [
    {value: 'GRCh37', display: 'hg19'},
    {value: 'GRCh38', display: 'GRCh38'}
];

var AutocompleteBox = createReactClass({
    render: function() {
        var terms = this.props.auto['@graph']; // List of matching terms from server
        var userTerm = this.props.userTerm && this.props.userTerm.toLowerCase(); // Term user entered

        if (!this.props.hide && userTerm && userTerm.length && terms && terms.length) {
            return (
                <ul className="adv-search-autocomplete">
                    {terms.map(function(term) {
                        var matchStart, matchEnd;
                        var preText, matchText, postText;

                        // Boldface matching part of term
                        matchStart = term.text.toLowerCase().indexOf(userTerm);
                        if (matchStart >= 0) {
                            matchEnd = matchStart + userTerm.length;
                            preText = term.text.substring(0, matchStart);
                            matchText = term.text.substring(matchStart, matchEnd);
                            postText = term.text.substring(matchEnd);
                        } else {
                            preText = term.text;
                        }
                        return <li key={term.text} tabIndex="0" onClick={this.props.handleClick.bind(null, term.text, term.payload.id, this.props.name)}>{preText}<b>{matchText}</b>{postText}</li>;
                    }, this)}
                </ul>
            );
        } else {
            return null;
        }
    }
});

var AdvSearch = createReactClass({
    getInitialState: function() {
        return {
            disclosed: false,
            showAutoSuggest: false,
            searchTerm: '',
            coordinates: '',
            genome: regionGenomes[0].value,
            terms: {}
        };
    },

    contextTypes: {
        autocompleteTermChosen: PropTypes.bool,
        autocompleteHidden: PropTypes.bool,
        onAutocompleteHiddenChange: PropTypes.func,
        location_href: PropTypes.string
    },

    handleDiscloseClick: function(e) {
        this.setState({disclosed: !this.state.disclosed});
    },

    handleChange: function(e) {
        this.setState({showAutoSuggest: true, terms: {}});
        this.newSearchTerm = e.target.value;
    },

    handleAutocompleteClick: function(term, id, name) {
        var newTerms = {};
        var inputNode = this.refs.annotation;
        inputNode.value = term;
        newTerms[name] = id;
        this.setState({terms: newTerms});
        this.setState({showAutoSuggest: false});
        inputNode.focus();
        // Now let the timer update the terms state when it gets around to it.
    },

    handleAssemblySelect: function(event) {
        // Handle click in assembly-selection <select>
        this.setState({genome: event.target.value});
    },

    componentDidMount: function() {
        // Use timer to limit to one request per second
        this.timer = setInterval(this.tick, 1000);
    },

    componentWillUnmount: function() {
        clearInterval(this.timer);
    },

    tick: function() {
        if (this.newSearchTerm !== this.state.searchTerm) {
            this.setState({searchTerm: this.newSearchTerm});
        }
    },

    render: function() {
        var context = this.props.context;
        var id = url.parse(this.context.location_href, true);
        var region = id.query['region'] || '';
        return (
            <Panel>
                <PanelBody>
                    <form id="panel1" className="adv-search-form" ref="adv-search" role="form" autoComplete="off" aria-labelledby="tab1">
                        <input type="hidden" name="annotation" value={this.state.terms['annotation']} />
                        <div className="form-group">
                            <label>Enter coordinates or rsid</label>
                            <div className="input-group input-group-region-input-new">
                                <input ref="annotation" defaultValue={region} name="region" type="text" placeholder="Enter Search (e.g. rs7903146, chr8:118184783-118184783)
" className="form-control" onChange={this.handleChange} />
                                <div className="input-group-addon input-group-select-addon">
                                    <select value={this.state.genome} name="genome" onChange={this.handleAssemblySelect}>
                                        {regionGenomes.map(genomeId =>
                                            <option key={genomeId.value} value={genomeId.value}>{genomeId.display}</option>
                                        )}
                                    </select>
                                </div>
		                <input type="submit" value="Search" className="btn btn-sm btn-info pull-left"/>
                                {context.notification ?
                                    <p className="input-region-error">{context.notification}</p>
                                : null}
                            </div>
                        </div>
                    </form>
                    {context.coordinates ?
                        <p>Searched coordinates: <strong>{context.coordinates}</strong></p>
                    : null}
                </PanelBody>
            </Panel>
        );
    }
});

var RegionSearch = module.exports.RegionSearch = createReactClass({
    onFilter: function(e) {
        var search = e.currentTarget.getAttribute('href');
        this.props.onChange(search);
        e.stopPropagation();
        e.preventDefault();
    },
    contextTypes: {
        location_href: PropTypes.string,
        navigate: PropTypes.func,
        session: PropTypes.object,
    },
    render: function() {
        const visualizeLimit = 100;
        var context = this.props.context;
	var results = context['@graph'];
        var variants = context['regions'];
	var coordinates = variants.coordinates;
        var key = variants.coordinates && variants.state && variants.state;
        var columns = context['columns'];
        var notification = context['notification'];
        var assembly = ['hg19'];
        var files = [];
        var id = url.parse(this.context.location_href, true);
        var region = context['region'] || '';
        var searchBase = url.parse(this.context.location_href).search || '';
	console.log(searchBase)
        var trimmedSearchBase = searchBase.replace(/[\?|\&]limit=all/, "");
        var filters = context['filters'];
        var facets = context['facets'];
        var total = context['total'];
	var kp = context['query'];
	var genome = context['genome'];
	var chromosome = context['chromosome']
	var start = context['start'] - 5000
	var end = context['end'] + 5000
	const domain = 'http://www.type2diabetesgenetics.org/variantInfo/variantInfo/';
	const loggedIn = this.context.session && this.context.session['auth.userid'];
        var visualize_disabled = total > visualizeLimit;
	const listing = module.exports.listing = function (reactProps) {
	    let context;
	    let viewProps = reactProps;
	    if (reactProps['@id']) {
		context = reactProps;
		viewProps = { context: context, key: context['@id'] };
		}
	    const ListingView = globals.listing_views.lookup(viewProps.context);
	    return <ListingView {...viewProps} />;
	    };
        // Get a sorted list of batch hubs keys with case-insensitive sort
        var visualizeKeys = []; 
        if (context.visualize_batch && Object.keys(context.visualize_batch).length) {
            visualizeKeys = Object.keys(context.visualize_batch).sort((a, b) => {
                var aLower = a.toLowerCase();
                var bLower = b.toLowerCase();
                return (aLower > bLower) ? 1 : ((aLower < bLower) ? -1 : 0);
            });
        }
        return (
            <div>
                <h2>Search variants</h2>
                <AdvSearch {...this.props} />
                    {context['notification'] === 'Success' ?
                        <div className="panel data-display main-panel">
                            <div className="row">
                                <div className="col-sm-5 col-md-4 col-lg-3">
                                    <FacetList {...this.props} facets={facets} filters={filters}
                                        searchBase={searchBase ? searchBase + '&' : searchBase + '?'} onFilter={this.onFilter} />
                                </div>
                                <div className="col-sm-7 col-md-8 col-lg-9">
                                    <div>
                                        <h4>
                                            Showing {results.length} overlapping annotations
                                        </h4>
                                        <div className="results-table-control">

		     {context['download_elements'] ?
		     <DropdownButton title='Download Elements' label="downloadelements" wrapperClasses="results-table-button">
		      <DropdownMenu>
		      {context['download_elements'].map(link =>
							<a key={link} data-bypass="true" target="_blank" private-browsing="true" href={link}>
							{link.split('.').pop()}
							</a>
							)}
		      </DropdownMenu>
		      </DropdownButton>
		      : null}
		     <a className="btn btn-info btn-sm" target = "_blank" href = { `${domain}${kp}` }>Knowledge Portal</a>
		     
</div>
</div> 
                                  <hr />
		                  <Panel>
		                  <TabPanel tabs={{ table: <h5> Results </h5>, graph: <h5> Variant Network </h5> }}>
                                  <TabPanelPane key="table">
                                  <ul className="nav result-table" id="result-table">
                                      {results.map(function (result) {
                                          return (
					      <li key={result['@id']}>
						  <div className="clearfix">
						  <div className="pull-right search-meta">
						  <p className="type">Annotation accession</p>
						  <p className="type">{result['accession']}</p>
						  </div>
						  <div class="accession">
						  <a href={result['@id']}><h4><font color="#428bca">Annotation Dataset: {result.description}</font></h4></a>
						  </div>
						  <div class="data-row">
						  <div><strong>Annotation type: </strong>{result.annotation_type}</div>
						  <div><strong>Biosample: </strong>{result.biosample_term_name}</div>
						  <div style={{'height': '100px', 'overflow-y':'scroll', 'display': 'block'}}><table className="table table-panel table-striped table-hover"><thead><tr><th>Overlapping Coordinate</th><th>State</th><th>Value</th></tr></thead><tbody>{variants.map(function (result_variant){ while (result['accession'] == result_variant['@id']) {return(<tr key={key}><td>{result_variant.coordinates}</td><td> {result_variant.state}</td><td> {result_variant.value}</td></tr>);																				       }})}
					      </tbody>
						  </table>
					      </div>
						  <br/>
						  </div>
						  </div>
						  </li>
						 
					  );
					  })}
					  </ul>
                                          </TabPanelPane>
                                          <TabPanelPane key="graph">
						      <FileGallery context={context} session={this.context.session} />
						    
                                          </TabPanelPane>
                                          </TabPanel>
                                          </Panel>
                                </div>
                            </div>
                        </div>
                    : null}            
						  </div>
        );
    }
});

globals.content_views.register(RegionSearch, 'variant-search');
