import React from 'react';
import PropTypes from 'prop-types';
import _ from 'underscore';
var url = require('url');
import moment from 'moment';
import { FetchedData, FetchedItems, Param } from './fetched';
import { Panel, PanelBody } from '../libs/bootstrap/panel';


// Main page component to render the home page
export default class Home extends React.Component {
    constructor(props) {
        super(props);
        // Set initial React state.
        this.state = {
            socialHeight: 600,
        };
    }
    render() {
        // Based on the currently selected organisms and assay category, generate a query string
        // for the GET request to retrieve chart data.
        return (
            <div className="whole-page">
                <div className="row">
                    <div className="col-xs-12">
                        <Panel>
                        <div ref="graphdisplay">
                        <div className="overall-classic">
                        <div className="site-banner">
		        <img src="/static/img/logo.png" alt="logo"/>
                        </div>
                        </div>
                        </div>
                        <div className="row">
                        </div>
                        <div ref="graphdisplay">
                        <div className="overall-classic">
                        <div className="site-tools">
                        <div className="site-banner-intro">
                        <div className="site-search">Search meta-data:
                        <Search />
                        </div>
                        <div className="site-search">Browse data:<br/>
                        </div>
                        </div>
                        <div className="site-banner-text">
<div className="site-search">Annotate genetic variants:<a className="btn-lg btn-tools" href = { 'http://www.demo.commondiseaseepigenome.org/variant-search/' } style= {{ 'font-size': '14px', 'font-family': 'Helvetica Neue,Helvetica,Arial,sans-serif', 'margin-top': '5px', 'margin-left':'20px', 'word-break': 'break-word', 'display': '-webkit-inline-box','justify-content': 'center', 'text-align': 'center', 'align-items': 'center'}} title="search">GO</a></div>
<div className="site-search">Single cell browser:<a className="btn-lg btn-tools" href = { 'http://www.single-cell.commondiseaseepigenome.org:5005' } style= {{ 'font-size': '14px', 'font\
-family': 'Helvetica Neue,Helvetica,Arial,sans-serif', 'margin-top': '5px', 'margin-left':'80px', 'word-break': 'break-word', 'display': '-webkit-inline-box','justify-content': 'center', 'text-align': 'center', 'align-items': 'center'}} title="search">GO</a></div>
<div className="site-search">Gene expression browser:<a className="btn-lg btn-tools" href = { 'http://www.tools.lungepigenome.org:3838/RShiny/' } style= {{ 'font-size': '14px', 'font-family': 'Helvetica Neue,Helvetica,Arial,sans-serif', 'margin-top': '5px', 'margin-left':'20px', 'word-break': 'break-word', 'display': '-webkit-inline-box','justify-content': 'center', 'text-align': 'center', 'align-items': 'center'}} title="search">GO</a></div>
                        </div>
                        </div>
                        </div>
                        </div>
                        <div className="row">
                        </div>                     
                                 <div className="social">
                                <h6 style= {{ 'font-size': '1.3rem', 'font-weight':'normal', 'font-family': 'Helvetica Neue,Helvetica,Arial,sans-serif', 'margin-top': '50px', 'margin-left':'50px', 'word-break': 'break-word', 'display': '-webkit-inline-box'}}>The <a href='https://fnih.org/our-programs/amp/accelerating-medicines-common-metabolic-diseases'>AMP CMD Consortium</a> is a collaboration among the following organizations, which also provide funding and/or governance:</h6>
                                <div className="social-news">
                                <img src="/static/img/thumbnail_nih_2021.png" alt="logo"/>
                                <img src="/static/img/thumbnail_fnih_2021.png" alt="logo"/>
                                <img src="/static/img/thumbnail_amgen_2021.png" alt="logo"/>
                                <img src="/static/img/thumbnail_lilly_2021.png" alt="logo"/>
                                <img src="/static/img/thumbnail_nordisk_2021.png" alt="logo"/>
                                <img src="/static/img/thumbnail_pfizer_2021.png" alt="logo"/>
                                </div>		
                            </div>
                        </Panel>
                    </div>
                </div>
            </div>
        );
    }
}
class SearchEngine extends React.Component {
render()
{
return <Search />
}
}

SearchEngine.contextTypes = {
    location_href: PropTypes.string,
};

const Search = (props, context) => {
    const id = url.parse(context.location_href, true);
    const searchTerm = id.query.searchTerm || '';
    return (
        <form className="home-form" action="/search/">
            <div className="search-wrapper">
                <span>
                <input
                    className="form-control search-query"
                    id="home-search"
                    type="text"
                    name="searchTerm"
                    defaultValue={searchTerm}
                    key={searchTerm}
                />
            <input type="submit" value="GO" className="btn btn-search" style={{'margin-left': '25px', 'margin-right': '10px'}} />
            </span>
            </div>
        </form>
    );
};

Search.contextTypes = {
    location_href: PropTypes.string,
};
const regionGenomes = [
    { value: 'GRCh37', display: 'hg19' },
    { value: 'GRCh38', display: 'GRCh38' }
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
                    
                    <form id="home-form"  ref="adv-search" role="form" autoComplete="off" aria-labelledby="tab1" action="/variant-search/">
                        <input type="hidden" name="annotation" value={this.state.terms.annotation} />
                        <div className="form-group">
                          <h4> Search variants & coordinates: </h4>
                            <div className="input-group input-group-region-input">
                                <input id="annotation" ref={(input) => { this.annotation = input; }} defaultValue={region} name="region" type="text" className="form-control" onChange={this.handleChange} />
                                <div className="input-group-addon input-group-select-addon">
                                    <select value={this.state.genome} name="genome" onChange={this.handleAssemblySelect}>
                                        {regionGenomes.map(genomeId =>
                                            <option key={genomeId.value} value={genomeId.value}>{genomeId.display}</option>
                                        )}
                                    </select>
                                </div>
                               <input type="submit" value="GO" className="submit_4 pull-right" style={{'margin-left': '30px', 'margin-right': '30px'}} />
                               </div>
                               </div>
		    <h5 style={{'margin-left': '10px', 'margin-top': '0px', 'font-weight': 'normal', 'font-style': 'italic'}}>example: <a href='variant-search/?region=rs7903146&genome=GRCh37'>rs7903146</a>, <a href='variant-search/?region=chr10%3A66794059&genome=GRCh37'>chr10:66794059</a></h5>
                    </form>
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
