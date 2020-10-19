import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

import AsyncSelect from 'react-select/async';

import { fetchUsers } from '../../utils/users';
import { HiddenCheckbox } from '../forms/Inputs';
import DeleteButton from '../forms/DeleteButton';
import { ErrorList, Wrapper } from '../forms/Utils';

const ENDPOINT = '/accounts/api/users';

const getUsers = (inputValue) => fetchUsers(inputValue, ENDPOINT);

const isEmpty = (obj) => {
    if (!obj) {
        return true;
    }
    return Object.keys(obj).length === 0;
};

const extractErrors = (errList) => errList.map((err) => err.msg);

const UserSelect = ({
    index, totalStepsIndex, data: { errors }, onDelete,
}) => {
    const [selectedData, setSelectedData] = useState(null);
    const [hiddenInputs, setHiddenInputs] = useState(null);

    // Create hidden inputs of the selected users
    const getHiddenInputs = (selectedUsers) => {
        const inputs = selectedUsers
            ? selectedUsers.map((user) => <HiddenCheckbox name="kownsl_users" value={user.value} key={user.value} checked required />)
            : <HiddenCheckbox name="kownsl_users" checked={false} required />;
        setHiddenInputs(inputs);
    };

    useEffect(() => {
        getHiddenInputs(selectedData);
    }, [selectedData]);

    return (
        <div className="user-select">
            { (errors && !isEmpty(errors.__all__))
                ? (
                    <Wrapper errors={errors.__all__}>
                        <ErrorList errors={extractErrors(errors.__all__)} />
                    </Wrapper>
                ) : null}

            <div className="user-select__title">
                { (totalStepsIndex !== 0)
                && <h3>{`Stap ${index + 1}`}</h3> }

                { (index === totalStepsIndex && index !== 0)
                && <DeleteButton onDelete={onDelete} /> }
            </div>
            {hiddenInputs}
            <div className="user-select__selector">
                <AsyncSelect
                    isMulti
                    cacheOptions
                    placeholder="Selecteer adviseur(s)"
                    name={`kownsl_users${-index}`}
                    defaultOptions={false}
                    loadOptions={getUsers}
                    onChange={(value) => setSelectedData(value)}
                />
            </div>
        </div>
    );
};

UserSelect.propTypes = {
    index: PropTypes.number.isRequired,
    totalStepsIndex: PropTypes.number,
    data: PropTypes.objectOf(PropTypes.object).isRequired,
    onDelete: PropTypes.func,
};

export default UserSelect;
