// Based on https://github.com/fullstackreact/food-lookup-demo
import React from "react";
import Client from "./Client";

const MATCHING_ITEM_LIMIT = 25;

class WineSearch extends React.Component {
    state = {
        wines: [],
        showRemoveIcon: false,
        searchValue: ""
    };

    handleSearchChange = e => {
        const value = e.target.value;

        this.setState({
            searchValue: value
        });

        if (value === "") {
            this.setState({
                wines: [],
                showRemoveIcon: false
            });
        } else {
            this.setState({
                showRemoveIcon: true
            });

            Client.search(value, wines => {
                this.setState({
                    wines: wines.slice(0, MATCHING_ITEM_LIMIT)
                });
            });
        }
    };

    handleSearchCancel = () => {
        this.setState({
            wines: [],
            showRemoveIcon: false,
            searchValue: ""
        });
    };

    render() {
        const {showRemoveIcon, wines} = this.state;
        const removeIconStyle = showRemoveIcon ? {} : {visibility: "hidden"};

        const wineCompanyRows = wines.map((wineCompany, idx) => (
            <tr key={idx} onClick={() => this.props.onWineClick(wineCompany)}>
                <td>{wineCompany.description}</td>
                <td className="right aligned">{wineCompany.company_name}</td>
                <td className="right aligned">{wineCompany.country}</td>
                <td className="right aligned">{wineCompany.status}</td>
            </tr>
        ));

        return (
            <div id="wine-search">
                <table className="ui selectable structured large table">
                    <thead>
                    <tr>
                        <th colSpan="5">
                            <div className="ui fluid search">
                                <div className="ui icon input">
                                    <input
                                        className="prompt"
                                        type="text"
                                        placeholder="Search wines..."
                                        value={this.state.searchValue}
                                        onChange={this.handleSearchChange}
                                    />
                                    <i className="search icon"/>
                                </div>
                                <i
                                    className="remove icon"
                                    onClick={this.handleSearchCancel}
                                    style={removeIconStyle}
                                />
                            </div>
                        </th>
                    </tr>
                    <tr>
                        <th className="eight wide">Description</th>
                        <th>Name</th>
                        <th>Country</th>
                        <th>Status</th>
                    </tr>
                    </thead>
                    <tbody>
                    {wineCompanyRows}
                    </tbody>
                </table>
            </div>
        );
    }
}

export default WineSearch;