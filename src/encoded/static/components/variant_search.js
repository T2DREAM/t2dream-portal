import React from 'react';
import PropTypes from 'prop-types';
import url from 'url';
import DropdownButton from '../libs/bootstrap/button';
import { DropdownMenu } from '../libs/bootstrap/dropdown-menu';
import { Panel, PanelBody } from '../libs/bootstrap/panel';
import { FacetList, Listing } from './search';
import { FetchedData, Param } from './fetched';
import * as globals from './globals';


const regionGenomes = [
    { value: 'GRCh37', display: 'hg19' },
];


const AutocompleteBox = (props) => {
    const terms = props.auto['@graph']; // List of matching terms from server
    const handleClick = props.handleClick;
    const userTerm = props.userTerm && props.userTerm.toLowerCase(); // Term user entered

    if (!props.hide && userTerm && userTerm.length && terms && terms.length) {
        return (
            <ul className="adv-search-autocomplete">
                {terms.map((term) => {
                    let matchEnd;
                    let preText;
                    let matchText;
                    let postText;

                    // Boldface matching part of term
                    const matchStart = term.text.toLowerCase().indexOf(userTerm);
                    if (matchStart >= 0) {
                        matchEnd = matchStart + userTerm.length;
                        preText = term.text.substring(0, matchStart);
                        matchText = term.text.substring(matchStart, matchEnd);
                        postText = term.text.substring(matchEnd);
                    } else {
                        preText = term.text;
                    }
                    return (
                        <AutocompleteBoxMenu
                            key={term.text}
                            handleClick={handleClick}
                            term={term}
                            name={props.name}
                            preText={preText}
                            matchText={matchText}
                            postText={postText}
                        />
                    );
                }, this)}
            </ul>
        );
    }

    return null;
};

AutocompleteBox.propTypes = {
    auto: PropTypes.object,
    userTerm: PropTypes.string,
    handleClick: PropTypes.func,
    hide: PropTypes.bool,
    name: PropTypes.string,
};

AutocompleteBox.defaultProps = {
    auto: {}, // Looks required, but because it's built from <Param>, it can fail type checks.
    userTerm: '',
    handleClick: null,
    hide: false,
    name: '',
};


// Draw the autocomplete box drop-down menu.
class AutocompleteBoxMenu extends React.Component {
    constructor() {
        super();

        // Bind this to non-React methods.
        this.handleClick = this.handleClick.bind(this);
    }

    // Handle clicks in the drop-down menu. It just calls the parent's handleClick function, giving
    // it the parameters of the clicked item.
    handleClick() {
        const { term, name } = this.props;
        this.props.handleClick(term.text, term._source.payload.id, name);
    }

    render() {
        const { preText, matchText, postText } = this.props;

        return (
            <li tabIndex="0" onClick={this.handleClick}>
                {preText}<b>{matchText}</b>{postText}
            </li>
        );
    }
}

AutocompleteBoxMenu.propTypes = {
    handleClick: PropTypes.func.isRequired, // Parent function to handle a click in a drop-down menu item
    term: PropTypes.object.isRequired, // Object for the term being searched
    name: PropTypes.string,
    preText: PropTypes.string, // Text before the matched term in the entered string
    matchText: PropTypes.string, // Matching text in the entered string
    postText: PropTypes.string, // Text after the matched term in the entered string
};

AutocompleteBoxMenu.defaultProps = {
    name: '',
    preText: '',
    matchText: '',
    postText: '',
};


class AdvSearch extends React.Component {
    constructor() {
        super();

        // Set intial React state.
        this.state = {
            disclosed: false,
            showAutoSuggest: false,
            searchTerm: '',
            coordinates: '',
            genome: regionGenomes[0].value,
            terms: {},
        };

        // Bind this to non-React methods.
        this.handleDiscloseClick = this.handleDiscloseClick.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.handleAutocompleteClick = this.handleAutocompleteClick.bind(this);
        this.handleAssemblySelect = this.handleAssemblySelect.bind(this);
        this.tick = this.tick.bind(this);
    }

    componentDidMount() {
        // Use timer to limit to one request per second
        this.timer = setInterval(this.tick, 1000);
    }

    componentWillUnmount() {
        clearInterval(this.timer);
    }

    handleDiscloseClick() {
        this.setState(prevState => ({
            disclosed: !prevState.disclosed,
        }));
    }

    handleChange(e) {
        this.setState({ showAutoSuggest: true, terms: {} });
        this.newSearchTerm = e.target.value;
    }

    handleAutocompleteClick(term, id, name) {
        const newTerms = {};
        const inputNode = this.annotation;
        inputNode.value = term;
        newTerms[name] = id;
        this.setState({ terms: newTerms, showAutoSuggest: false });
        inputNode.focus();
        // Now let the timer update the terms state when it gets around to it.
    }

    handleAssemblySelect(event) {
        // Handle click in assembly-selection <select>
        this.setState({ genome: event.target.value });
    }

    tick() {
        if (this.newSearchTerm !== this.state.searchTerm) {
            this.setState({ searchTerm: this.newSearchTerm });
        }
    }

    render() {
        const context = this.props.context;
        const id = url.parse(this.context.location_href, true);
        const region = id.query.region || '';

        return (
            <Panel>
                <PanelBody>
                    <form id="panel1" className="adv-search-form" ref="adv-search" role="form" autoComplete="off" aria-labelledby="tab1">
                        <input type="hidden" name="annotation" value={this.state.terms.annotation} />
                        <div className="form-group">
                            <label htmlFor="annotation" >Enter coordinates or rsid</label>
                            <div className="input-group input-group-region-input">
                                <input id="annotation" ref={(input) => { this.annotation = input; }} defaultValue={region} name="region" type="text" className="form-control" onChange={this.handleChange} />
                                <div className="input-group-addon input-group-select-addon">
                                    <select value={this.state.genome} name="genome" onChange={this.handleAssemblySelect}>
                                        {regionGenomes.map(genomeId =>
                                            <option key={genomeId.value} value={genomeId.value}>{genomeId.display}</option>
                                        )}
                                    </select>
                                </div>
                                {context.notification ?
                                    <p className="input-region-error">{context.notification}</p>
                                : null}
                            </div>
                        </div>
                        <input type="submit" value="Search" className="btn btn-sm btn-info pull-right" />
                    </form>
                    {context.coordinates ?
                        <p>Searched coordinates: <strong>{context.coordinates}</strong></p>
                    : null}
                </PanelBody>
            </Panel>
        );
    }
}

AdvSearch.propTypes = {
    context: PropTypes.object.isRequired,
};

AdvSearch.contextTypes = {
    autocompleteTermChosen: PropTypes.bool,
    autocompleteHidden: PropTypes.bool,
    onAutocompleteHiddenChange: PropTypes.func,
    location_href: PropTypes.string,
};


class VariantSearch extends React.Component {
    constructor() {
        super();

        // Bind this to non-React methods.
        this.onFilter = this.onFilter.bind(this);
    }

    onFilter(e) {
        if (this.props.onChange) {
            const search = e.currentTarget.getAttribute('href');
            this.props.onChange(search);
            e.stopPropagation();
            e.preventDefault();
        }
    }

    render() {
        const visualizeLimit = 100;
        const context = this.props.context;
        const results = context['@graph'];
        const columns = context.columns;
	const variants = context['regions'];
	const coordinates = variants.coordinates;
	const key = variants.coordinates && variants.state_annotation && variants.value_annotation;
        const notification = context.notification;
	const assembly = ['hg19'];
	const files = [];
	const id = url.parse(this.context.location_href, true);
	const region = context['region'] || '';
        const searchBase = url.parse(this.context.location_href).search || '';
        const trimmedSearchBase = searchBase.replace(/[?|&]limit=all/, '');
        const filters = context.filters;
        const facets = context.facets;
        const total = context.total;
	var genome = context['genome'];
	var chromosome = context['chromosome']
	var start = context['start'] - 5000
	var end = context['end'] + 5000
	const loggedIn = this.context.session && this.context.session['auth.userid'];
        const visualizeDisabled = total > visualizeLimit;

        // Get a sorted list of batch hubs keys with case-insensitive sort
        let visualizeKeys = [];
        if (context.visualize_batch && Object.keys(context.visualize_batch).length) {
            visualizeKeys = Object.keys(context.visualize_batch).sort((a, b) => {
                const aLower = a.toLowerCase();
                const bLower = b.toLowerCase();
                return (aLower > bLower) ? 1 : ((aLower < bLower) ? -1 : 0);
            });
        }

        return (
            <div>
                <h2>Variant search</h2>
                <AdvSearch {...this.props} />
                    {notification === 'Success' ?
                        <div className="panel data-display main-panel">
                            <div className="row">
                                <div className="col-sm-5 col-md-4 col-lg-3">
                                    <FacetList
                                        {...this.props}
                                        facets={facets}
                                        filters={filters}
                                        searchBase={searchBase ? `${searchBase}&` : `${searchBase}?`}
                                        onFilter={this.onFilter}
                                    />
                                </div>
                                <div className="col-sm-7 col-md-8 col-lg-9">
                                    <div>
                                        <h4>
                                            Showing {results.length} of {total}
                                        </h4>
                                        <div className="results-table-control">
                                            {total > results.length && searchBase.indexOf('limit=all') === -1 ?
                                                    <a
                                                        rel="nofollow"
                                                        className="btn btn-info btn-sm"
                                                        href={searchBase ? `${searchBase}&limit=all` : '?limit=all'}
                                                        onClick={this.onFilter}
                                                    >
                                                        View All
                                                    </a>
                                            :
                                                <span>
                                                    {results.length > 25 ?
                                                            <a
                                                                className="btn btn-info btn-sm"
                                                                href={trimmedSearchBase || '/variant-search/'}
                                                                onClick={this.onFilter}
                                                            >
                                                                View 25
                                                            </a>
                                                    : null}
                                                </span>
                                            }
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
                                        </div>
                                    </div>

                                  <hr />
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
						  <div style={{'height': '100px', 'overflow-y':'scroll', 'display': 'block'}}><table className="table table-panel table-striped table-hover"><thead><tr><th>Overlapping Coordinate</th><th>State</th><th>Value</th></tr></thead><tbody>{variants.map(function (result_variant){ while (result['accession'] == result_variant['@id']) {return(<tr key={key}><td>{result_variant.coordinates}</td><td> {result_variant.state_annotation}</td><td> {result_variant.value_annotation}</td></tr>);																				       }})}
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
                                </div>
                            </div>
                        </div>
                    : null}
            </div>
        );
    }
}

VariantSearch.propTypes = {
    context: PropTypes.object.isRequired,
    onChange: PropTypes.func,
};

VariantSearch.defaultProps = {
    onChange: null,
};

VariantSearch.contextTypes = {
    location_href: PropTypes.string,
    navigate: PropTypes.func,
};

globals.contentViews.register(VariantSearch, 'variant-search');
